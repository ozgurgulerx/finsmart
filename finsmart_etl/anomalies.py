"""
Anomaly Detection: Smart detection using YoY + Rolling Average + LLM reasoning.

Detection methods:
1. Year-over-Year (YoY): Compare to same month last year
2. Rolling Average: Compare to trailing 3-month average
3. Composite Score: Weighted combination of both signals
4. LLM Reasoning: Use gpt-5-nano to explain why it's an anomaly
"""

import json
from typing import Optional
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from openai import OpenAI

from .config import get_config

# Thresholds
YOY_THRESHOLD_PCT = 30.0  # Year-over-year change threshold
ROLLING_THRESHOLD_PCT = 25.0  # Deviation from 3-month rolling avg
ZSCORE_THRESHOLD = 2.0  # Standard deviations from mean


def detect_anomalies(
    conn: psycopg.Connection,
    company_id: UUID,
    yoy_threshold: float = YOY_THRESHOLD_PCT,
    rolling_threshold: float = ROLLING_THRESHOLD_PCT
) -> int:
    """
    Detect anomalies using hybrid approach:
    1. YoY comparison (same month last year)
    2. Rolling 3-month average comparison
    3. Z-score from 6-month historical mean
    
    An anomaly is flagged if YoY OR rolling avg deviation exceeds threshold.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        yoy_threshold: YoY percentage threshold
        rolling_threshold: Rolling average deviation threshold
    
    Returns:
        int: Number of anomalies detected/upserted
    """
    query = """
        WITH base AS (
            SELECT
                company_id,
                metric_name,
                month,
                value,
                -- Previous month (MoM)
                LAG(value, 1) OVER w AS prev_month_value,
                -- Same month last year (YoY)
                LAG(value, 12) OVER w AS yoy_value,
                -- Rolling 3-month average (excluding current)
                AVG(value) OVER (
                    PARTITION BY company_id, metric_name 
                    ORDER BY month
                    ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
                ) AS rolling_3m_avg,
                -- Rolling 6-month stats for z-score
                AVG(value) OVER (
                    PARTITION BY company_id, metric_name 
                    ORDER BY month
                    ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING
                ) AS rolling_6m_avg,
                STDDEV(value) OVER (
                    PARTITION BY company_id, metric_name 
                    ORDER BY month
                    ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING
                ) AS rolling_6m_stddev
            FROM monthly_kpis
            WHERE company_id = %s
            WINDOW w AS (PARTITION BY company_id, metric_name ORDER BY month)
        ),
        metrics AS (
            SELECT
                company_id,
                metric_name,
                month,
                value AS curr_value,
                prev_month_value,
                yoy_value,
                rolling_3m_avg,
                rolling_6m_avg,
                rolling_6m_stddev,
                -- MoM change
                CASE WHEN prev_month_value != 0 AND prev_month_value IS NOT NULL
                     THEN (value - prev_month_value) / ABS(prev_month_value) * 100
                     ELSE NULL END AS mom_pct,
                -- YoY change
                CASE WHEN yoy_value != 0 AND yoy_value IS NOT NULL
                     THEN (value - yoy_value) / ABS(yoy_value) * 100
                     ELSE NULL END AS yoy_pct,
                -- Rolling avg deviation
                CASE WHEN rolling_3m_avg != 0 AND rolling_3m_avg IS NOT NULL
                     THEN (value - rolling_3m_avg) / ABS(rolling_3m_avg) * 100
                     ELSE NULL END AS rolling_pct,
                -- Z-score
                CASE WHEN rolling_6m_stddev > 0
                     THEN (value - rolling_6m_avg) / rolling_6m_stddev
                     ELSE NULL END AS zscore
            FROM base
        ),
        anomalies_detected AS (
            SELECT
                company_id,
                metric_name,
                month,
                prev_month_value,
                curr_value,
                yoy_value,
                rolling_3m_avg,
                mom_pct,
                yoy_pct,
                rolling_pct,
                zscore,
                -- Primary: use MoM for display (what changed from last month)
                mom_pct AS pct_change,
                -- Composite severity score
                GREATEST(
                    COALESCE(ABS(yoy_pct), 0),
                    COALESCE(ABS(rolling_pct), 0),
                    COALESCE(ABS(zscore) * 15, 0)  -- Scale z-score to comparable range
                ) AS severity_score,
                -- Detection reason
                CASE
                    WHEN ABS(yoy_pct) >= %s AND ABS(rolling_pct) >= %s THEN 'yoy_and_rolling'
                    WHEN ABS(yoy_pct) >= %s THEN 'yoy'
                    WHEN ABS(rolling_pct) >= %s THEN 'rolling'
                    WHEN ABS(zscore) >= 2.0 THEN 'zscore'
                    ELSE NULL
                END AS detection_reason
            FROM metrics
        )
        INSERT INTO anomalies (
            company_id, month, metric_name,
            prev_value, curr_value, pct_change,
            severity_score, status, meta
        )
        SELECT
            company_id,
            month,
            metric_name,
            prev_month_value,
            curr_value,
            pct_change,
            severity_score,
            'open',
            jsonb_build_object(
                'detection_reason', detection_reason,
                'yoy_value', yoy_value,
                'yoy_pct', yoy_pct,
                'rolling_3m_avg', rolling_3m_avg,
                'rolling_pct', rolling_pct,
                'zscore', zscore
            )
        FROM anomalies_detected
        WHERE detection_reason IS NOT NULL
        ON CONFLICT (company_id, month, metric_name) DO UPDATE
        SET prev_value     = EXCLUDED.prev_value,
            curr_value     = EXCLUDED.curr_value,
            pct_change     = EXCLUDED.pct_change,
            severity_score = EXCLUDED.severity_score,
            meta           = EXCLUDED.meta
        RETURNING id
    """
    
    with conn.cursor() as cur:
        cur.execute(query, (
            str(company_id),
            yoy_threshold, rolling_threshold,  # for yoy_and_rolling
            yoy_threshold,  # for yoy only
            rolling_threshold  # for rolling only
        ))
        rows = cur.fetchall()
        conn.commit()
        
    count = len(rows)
    print(f"Detected {count} anomalies (YoY ≥{yoy_threshold}% OR Rolling ≥{rolling_threshold}%)")
    return count


def explain_anomaly_detection(anomaly: dict) -> str:
    """
    Use gpt-5-nano to explain why this was flagged as an anomaly.
    
    Args:
        anomaly: Anomaly dict with meta containing detection details
    
    Returns:
        str: LLM-generated explanation of why it's an anomaly
    """
    config = get_config()
    client = OpenAI(api_key=config.openai_api_key)
    
    meta = anomaly.get("meta") or {}
    if isinstance(meta, str):
        meta = json.loads(meta)
    if meta is None:
        meta = {}
    
    # Safely format values that might be None
    yoy_pct = meta.get('yoy_pct')
    rolling_pct = meta.get('rolling_pct')
    zscore = meta.get('zscore')
    
    yoy_str = f"{yoy_pct:.1f}%" if yoy_pct is not None else "N/A"
    rolling_str = f"{rolling_pct:.1f}%" if rolling_pct is not None else "N/A"
    zscore_str = f"{zscore:.2f}" if zscore is not None else "N/A"
    
    prompt = f"""You are a financial analyst. Explain briefly (2 sentences) why this metric was flagged as an anomaly.

METRIC: {anomaly.get('metric_name')}
MONTH: {anomaly.get('month')}
CURRENT VALUE: {anomaly.get('curr_value')}
PREVIOUS MONTH: {anomaly.get('prev_value')}
SAME MONTH LAST YEAR: {meta.get('yoy_value', 'N/A')}
3-MONTH ROLLING AVG: {meta.get('rolling_3m_avg', 'N/A')}

DETECTION SIGNALS:
- YoY Change: {yoy_str} (threshold: ±{YOY_THRESHOLD_PCT}%)
- Rolling Avg Deviation: {rolling_str} (threshold: ±{ROLLING_THRESHOLD_PCT}%)
- Z-Score: {zscore_str} (threshold: ±2.0)
- Detection Reason: {meta.get('detection_reason', 'unknown')}

Explain in plain English why this is considered anomalous. Be specific about which signals triggered the detection."""

    try:
        result = client.responses.create(
            model="gpt-5-nano",
            input=prompt,
            reasoning={"effort": "low"},
            text={"verbosity": "low"},
        )
        return result.output_text.strip()
    except Exception as e:
        # Fallback to rule-based explanation
        reason = meta.get('detection_reason', 'unknown') if meta else 'unknown'
        if reason == 'yoy_and_rolling':
            return f"Flagged because both YoY ({yoy_str}) and rolling average deviation ({rolling_str}) exceed thresholds."
        elif reason == 'yoy':
            return f"Flagged due to significant year-over-year change of {yoy_str} compared to same month last year."
        elif reason == 'rolling':
            return f"Flagged because value deviates {rolling_str} from the trailing 3-month average."
        elif reason == 'zscore':
            return f"Flagged as statistical outlier with z-score of {zscore_str} (>2 standard deviations from mean)."
        return f"Anomaly detected (legacy data without detection metadata)"


def get_anomalies_for_month(
    conn: psycopg.Connection,
    company_id: UUID,
    month: str  # YYYY-MM-DD format
) -> list[dict]:
    """
    Get all anomalies for a specific month.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        month: Month as string (YYYY-MM-DD, first of month)
    
    Returns:
        List of anomaly dictionaries
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT 
                id, month, metric_name, 
                prev_value, curr_value, pct_change,
                severity_score, status, meta, created_at
            FROM anomalies
            WHERE company_id = %s AND month = %s
            ORDER BY severity_score DESC
            """,
            (str(company_id), month)
        )
        return cur.fetchall()


def get_anomalies_for_company(
    conn: psycopg.Connection,
    company_id: UUID,
    status: Optional[str] = None,
    limit: int = 100
) -> list[dict]:
    """
    Get all anomalies for a company.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        status: Optional filter by status ('open', 'muted', 'confirmed')
        limit: Maximum number of results
    
    Returns:
        List of anomaly dictionaries
    """
    query = """
        SELECT 
            id, month, metric_name, 
            prev_value, curr_value, pct_change,
            severity_score, status, created_at
        FROM anomalies
        WHERE company_id = %s
    """
    params = [str(company_id)]
    
    if status:
        query += " AND status = %s"
        params.append(status)
    
    query += " ORDER BY month DESC, severity_score DESC LIMIT %s"
    params.append(limit)
    
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_anomalies_without_contributors(
    conn: psycopg.Connection,
    company_id: Optional[UUID] = None,
    limit: int = 100
) -> list[dict]:
    """
    Get anomalies that don't have contributors computed yet.
    
    Args:
        conn: Database connection
        company_id: Optional company filter
        limit: Maximum number of results
    
    Returns:
        List of anomaly dictionaries
    """
    query = """
        SELECT a.id, a.company_id, a.month, a.metric_name,
               a.prev_value, a.curr_value, a.pct_change
        FROM anomalies a
        LEFT JOIN anomaly_contributors ac ON ac.anomaly_id = a.id
        WHERE ac.id IS NULL
    """
    params = []
    
    if company_id:
        query += " AND a.company_id = %s"
        params.append(str(company_id))
    
    query += " ORDER BY a.created_at DESC LIMIT %s"
    params.append(limit)
    
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_anomalies_without_highlights(
    conn: psycopg.Connection,
    company_id: Optional[UUID] = None,
    limit: int = 100
) -> list[dict]:
    """
    Get anomalies that don't have highlights generated yet.
    
    Args:
        conn: Database connection
        company_id: Optional company filter
        limit: Maximum number of results
    
    Returns:
        List of anomaly dictionaries
    """
    query = """
        SELECT a.id, a.company_id, a.month, a.metric_name,
               a.prev_value, a.curr_value, a.pct_change, a.severity_score
        FROM anomalies a
        LEFT JOIN anomaly_highlights ah ON ah.anomaly_id = a.id
        WHERE ah.id IS NULL
    """
    params = []
    
    if company_id:
        query += " AND a.company_id = %s"
        params.append(str(company_id))
    
    query += " ORDER BY a.severity_score DESC LIMIT %s"
    params.append(limit)
    
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchall()


def update_anomaly_status(
    conn: psycopg.Connection,
    anomaly_id: int,
    status: str
) -> bool:
    """
    Update the status of an anomaly.
    
    Args:
        conn: Database connection
        anomaly_id: Anomaly ID
        status: New status ('open', 'muted', 'confirmed')
    
    Returns:
        bool: True if updated, False if not found
    """
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE anomalies SET status = %s WHERE id = %s RETURNING id",
            (status, anomaly_id)
        )
        row = cur.fetchone()
        conn.commit()
        return row is not None
