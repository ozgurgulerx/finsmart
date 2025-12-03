"""
Anomaly Detection: Detect month-over-month changes ≥ 20%.

Uses SQL window functions to compute MoM changes and flag anomalies.
"""

from typing import Optional
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

# Threshold for flagging anomalies (percentage)
ANOMALY_THRESHOLD_PCT = 20.0


def detect_anomalies(
    conn: psycopg.Connection,
    company_id: UUID,
    threshold_pct: float = ANOMALY_THRESHOLD_PCT
) -> int:
    """
    Detect anomalies for all metrics of a company.
    
    An anomaly is flagged when |pct_change| >= threshold_pct.
    
    Uses SQL window functions (LAG) to compute MoM changes efficiently.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        threshold_pct: Percentage threshold for flagging anomalies
    
    Returns:
        int: Number of anomalies detected/upserted
    """
    query = """
        WITH series AS (
            SELECT
                company_id,
                metric_name,
                month,
                value,
                LAG(value) OVER (
                    PARTITION BY company_id, metric_name 
                    ORDER BY month
                ) AS prev_value
            FROM monthly_kpis
            WHERE company_id = %s
        ),
        changes AS (
            SELECT
                company_id,
                metric_name,
                month,
                prev_value,
                value AS curr_value,
                CASE
                    WHEN prev_value IS NULL OR prev_value = 0 THEN NULL
                    ELSE (value - prev_value) / ABS(prev_value) * 100.0
                END AS pct_change
            FROM series
        )
        INSERT INTO anomalies (
            company_id, month, metric_name,
            prev_value, curr_value, pct_change,
            severity_score, status
        )
        SELECT
            company_id,
            month,
            metric_name,
            prev_value,
            curr_value,
            pct_change,
            ABS(pct_change) AS severity_score,
            'open' AS status
        FROM changes
        WHERE pct_change IS NOT NULL
          AND ABS(pct_change) >= %s
        ON CONFLICT (company_id, month, metric_name) DO UPDATE
        SET prev_value     = EXCLUDED.prev_value,
            curr_value     = EXCLUDED.curr_value,
            pct_change     = EXCLUDED.pct_change,
            severity_score = EXCLUDED.severity_score
        RETURNING id
    """
    
    with conn.cursor() as cur:
        cur.execute(query, (str(company_id), threshold_pct))
        rows = cur.fetchall()
        conn.commit()
        
    count = len(rows)
    print(f"Detected {count} anomalies (threshold: ±{threshold_pct}%)")
    return count


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
                severity_score, status, created_at
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
