"""
CFO Month View: Comprehensive financial view for a company and month.

Provides:
- Metrics overview with MoM changes
- Anomaly details with contributors and explanations
- Evidence samples for human verification
"""

from datetime import date
from typing import Optional
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from .metrics import compute_monthly_kpis
from .anomalies import detect_anomalies, get_anomalies_for_month
from .contributors import (
    compute_contributors_for_company,
    get_contributors_for_anomaly,
    get_evidence_transactions,
)
from .explanations import (
    generate_highlights_for_new_anomalies,
    get_highlights_for_anomaly,
    generate_highlight_for_anomaly,
    month_label_tr,
    metric_name_tr,
    format_amount_tr,
)


def get_company_info(conn: psycopg.Connection, company_id: UUID) -> dict:
    """
    Get company information.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
    
    Returns:
        dict: Company info
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, finsmart_guid, name, business_model, created_at
            FROM companies
            WHERE id = %s
            """,
            (str(company_id),)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Company {company_id} not found")
        return dict(row)


def get_metrics_overview(
    conn: psycopg.Connection,
    company_id: UUID,
    month: date
) -> list[dict]:
    """
    Get all metrics for a month with MoM comparison.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        month: Target month (first of month)
    
    Returns:
        List of metric dictionaries with prev/curr/change
    """
    # Calculate previous month
    if month.month == 1:
        prev_month = month.replace(year=month.year - 1, month=12)
    else:
        prev_month = month.replace(month=month.month - 1)
    
    # Get current month KPIs
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT metric_name, value
            FROM monthly_kpis
            WHERE company_id = %s AND month = %s
            """,
            (str(company_id), month)
        )
        current_kpis = {row["metric_name"]: row["value"] for row in cur.fetchall()}
    
    # Get previous month KPIs
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT metric_name, value
            FROM monthly_kpis
            WHERE company_id = %s AND month = %s
            """,
            (str(company_id), prev_month)
        )
        prev_kpis = {row["metric_name"]: row["value"] for row in cur.fetchall()}
    
    # Get anomalies for this month
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT metric_name
            FROM anomalies
            WHERE company_id = %s AND month = %s
            """,
            (str(company_id), month)
        )
        anomaly_metrics = {row[0] for row in cur.fetchall()}
    
    # Build overview
    metrics = []
    all_metric_names = set(current_kpis.keys()) | set(prev_kpis.keys())
    
    for metric_name in sorted(all_metric_names):
        curr_val = current_kpis.get(metric_name)
        prev_val = prev_kpis.get(metric_name)
        
        # Calculate percentage change
        pct_change = None
        if prev_val and prev_val != 0 and curr_val is not None:
            pct_change = float((curr_val - prev_val) / abs(prev_val) * 100)
        
        metrics.append({
            "metric_name": metric_name,
            "metric_name_tr": metric_name_tr(metric_name),
            "prev_value": float(prev_val) if prev_val else None,
            "curr_value": float(curr_val) if curr_val else None,
            "prev_formatted": format_amount_tr(prev_val) if prev_val else "-",
            "curr_formatted": format_amount_tr(curr_val) if curr_val else "-",
            "pct_change": round(pct_change, 1) if pct_change else None,
            "is_anomalous": metric_name in anomaly_metrics,
        })
    
    return metrics


def get_anomaly_details(
    conn: psycopg.Connection,
    company_id: UUID,
    month: date,
    generate_missing_highlights: bool = True
) -> list[dict]:
    """
    Get detailed anomaly information for a month.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        month: Target month
        generate_missing_highlights: If True, generate highlights on-the-fly
    
    Returns:
        List of detailed anomaly dictionaries
    """
    anomalies = get_anomalies_for_month(conn, company_id, str(month))
    
    details = []
    for anomaly in anomalies:
        anomaly_id = anomaly["id"]
        
        # Get contributors
        contributors = get_contributors_for_anomaly(conn, anomaly_id)
        
        # Get highlights
        highlights = get_highlights_for_anomaly(conn, anomaly_id)
        
        # Generate missing highlights on-the-fly
        if generate_missing_highlights and not highlights.get("tr"):
            try:
                generate_highlight_for_anomaly(conn, anomaly_id)
                highlights = get_highlights_for_anomaly(conn, anomaly_id)
            except Exception as e:
                print(f"Could not generate highlights: {e}")
        
        # Get evidence sample
        evidence = get_evidence_transactions(
            conn, company_id, str(month), anomaly["metric_name"], limit=10
        )
        
        details.append({
            "metric_name": anomaly["metric_name"],
            "metric_name_tr": metric_name_tr(anomaly["metric_name"]),
            "prev_value": float(anomaly["prev_value"]) if anomaly["prev_value"] else None,
            "curr_value": float(anomaly["curr_value"]) if anomaly["curr_value"] else None,
            "prev_formatted": format_amount_tr(anomaly["prev_value"]) if anomaly["prev_value"] else "-",
            "curr_formatted": format_amount_tr(anomaly["curr_value"]) if anomaly["curr_value"] else "-",
            "pct_change": float(anomaly["pct_change"]) if anomaly["pct_change"] else None,
            "severity_score": float(anomaly["severity_score"]) if anomaly["severity_score"] else None,
            "status": anomaly["status"],
            "contributors": [
                {
                    "label": c["label"],
                    "amount": float(c["amount"]),
                    "amount_formatted": format_amount_tr(c["amount"]),
                    "share_pct": round(float(c["share_of_total"]) * 100, 1),
                }
                for c in contributors
            ],
            "highlights": highlights,
            "evidence_sample": [
                {
                    "date": str(e["tx_date"]),
                    "account_code": e["account_code"],
                    "account_name": e["account_name"],
                    "coa_code": e["coa_code"],
                    "coa_name": e["coa_name"],
                    "description": e["description"],
                    "customer_name": e["customer_name"],
                    "amount": float(e["amount"]),
                    "amount_formatted": format_amount_tr(e["amount"]),
                }
                for e in evidence
            ],
        })
    
    return details


def build_cfo_month_view(
    conn: psycopg.Connection,
    company_id: UUID,
    month: date,
    ensure_computed: bool = True,
    generate_highlights: bool = True
) -> dict:
    """
    Build comprehensive CFO view for a company and month.
    
    This is the main entrypoint for UI and agents.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        month: Target month (will be normalized to first of month)
        ensure_computed: If True, run compute pipeline first
        generate_highlights: If True, generate missing highlights
    
    Returns:
        dict: Complete CFO view with metrics, anomalies, and evidence
    """
    # Normalize month to first of month
    month = month.replace(day=1)
    
    # Ensure derived layers are computed (lazy safety)
    if ensure_computed:
        print("Ensuring metrics and anomalies are computed...")
        compute_monthly_kpis(conn, company_id)
        detect_anomalies(conn, company_id)
        compute_contributors_for_company(conn, company_id)
        
        if generate_highlights:
            generate_highlights_for_new_anomalies(conn, company_id, batch_size=10)
    
    # Get company info
    company = get_company_info(conn, company_id)
    
    # Get metrics overview
    metrics_overview = get_metrics_overview(conn, company_id, month)
    
    # Get anomaly details
    anomalies = get_anomaly_details(
        conn, company_id, month,
        generate_missing_highlights=generate_highlights
    )
    
    # Build summary
    total_anomalies = len(anomalies)
    positive_anomalies = sum(1 for a in anomalies if a["pct_change"] and a["pct_change"] > 0)
    negative_anomalies = total_anomalies - positive_anomalies
    
    return {
        "company": {
            "id": str(company["id"]),
            "finsmart_guid": str(company["finsmart_guid"]),
            "name": company["name"],
            "business_model": company["business_model"],
        },
        "month": str(month),
        "month_label_tr": month_label_tr(month),
        "summary": {
            "total_metrics": len(metrics_overview),
            "total_anomalies": total_anomalies,
            "positive_anomalies": positive_anomalies,
            "negative_anomalies": negative_anomalies,
        },
        "metrics_overview": metrics_overview,
        "anomalies": anomalies,
    }


def get_available_months(
    conn: psycopg.Connection,
    company_id: UUID
) -> list[str]:
    """
    Get list of months with data for a company.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
    
    Returns:
        List of month strings (YYYY-MM-DD format)
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT month
            FROM monthly_kpis
            WHERE company_id = %s
            ORDER BY month DESC
            """,
            (str(company_id),)
        )
        return [str(row[0]) for row in cur.fetchall()]


def get_company_by_guid(
    conn: psycopg.Connection,
    finsmart_guid: str
) -> Optional[dict]:
    """
    Get company by Finsmart GUID.
    
    Args:
        conn: Database connection
        finsmart_guid: Finsmart company GUID
    
    Returns:
        Company dict or None if not found
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM companies WHERE finsmart_guid = %s",
            (finsmart_guid,)
        )
        return cur.fetchone()
