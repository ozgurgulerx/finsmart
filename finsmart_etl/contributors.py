"""
Root-Cause Contributors: Compute top contributors for each anomaly.

Identifies which vendors/customers/line items drove the anomalous change.
"""

from typing import Optional
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from .metrics import get_metric_definition, METRIC_DEFINITIONS


def metric_filter_condition(metric_name: str) -> str:
    """
    Return a SQL WHERE condition snippet for a metric.
    
    Args:
        metric_name: Name of the metric
    
    Returns:
        str: SQL condition (without 'WHERE')
    
    Raises:
        ValueError: If metric not found
    """
    metric = get_metric_definition(metric_name)
    if metric:
        return metric.sql_filter
    
    # Fallback mappings for common metrics
    fallbacks = {
        "net_sales": "account_code LIKE '1.1%'",
        "advisory_expense": "(account_name = 'Advisory' OR coa_name ILIKE '%DANISMAN%')",
        "software_expense": "account_name = 'Software'",
        "payroll": "account_name = 'Payroll'",
        "marketing": "account_name = 'Marketing'",
        "hospitality": "account_name = 'Hospitality'",
        "office_rent": "account_name = 'Office Rent'",
        "car_expenses": "account_name = 'Car Expenses'",
        "food_expenses": "account_name = 'Food Expenses'",
    }
    
    if metric_name in fallbacks:
        return fallbacks[metric_name]
    
    # Generic fallback - match account_name
    return f"account_name = '{metric_name}'"


def compute_contributors_for_anomaly(
    conn: psycopg.Connection,
    anomaly_id: int,
    top_n: int = 10,
    coverage_threshold: float = 0.8
) -> int:
    """
    Compute top contributors for a single anomaly.
    
    Groups transactions by vendor/customer and identifies the top N that
    explain at least coverage_threshold (80%) of the total.
    
    Args:
        conn: Database connection
        anomaly_id: ID of the anomaly
        top_n: Maximum number of contributors to keep
        coverage_threshold: Target coverage (0-1)
    
    Returns:
        int: Number of contributors inserted
    """
    # Get anomaly details
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT company_id, month, metric_name, curr_value
            FROM anomalies
            WHERE id = %s
            """,
            (anomaly_id,)
        )
        anomaly = cur.fetchone()
        if not anomaly:
            raise ValueError(f"Anomaly {anomaly_id} not found")
    
    company_id = anomaly["company_id"]
    month = anomaly["month"]
    metric_name = anomaly["metric_name"]
    
    # Get filter condition for this metric
    try:
        filter_cond = metric_filter_condition(metric_name)
    except ValueError:
        print(f"Unknown metric {metric_name}, skipping contributors")
        return 0
    
    # Query transactions grouped by label
    query = f"""
        SELECT 
            COALESCE(NULLIF(customer_name, ''), NULLIF(description, ''), 'Unknown') AS label,
            SUM(amount) AS total_amount,
            COUNT(*) AS tx_count
        FROM transactions
        WHERE company_id = %s 
          AND month = %s
          AND {filter_cond}
        GROUP BY label
        ORDER BY ABS(SUM(amount)) DESC
        LIMIT %s
    """
    
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, (str(company_id), month, top_n * 2))  # Get extra to check coverage
        contributors = cur.fetchall()
    
    if not contributors:
        return 0
    
    # Calculate total and filter to top contributors
    total = sum(abs(c["total_amount"]) for c in contributors)
    if total == 0:
        return 0
    
    # Select contributors until we hit coverage threshold or top_n
    selected = []
    cumulative = 0
    for c in contributors:
        if len(selected) >= top_n:
            break
        share = abs(c["total_amount"]) / total
        selected.append({
            "label": c["label"],
            "amount": c["total_amount"],
            "share_of_total": share,
        })
        cumulative += share
        if cumulative >= coverage_threshold:
            break
    
    # Delete existing contributors for this anomaly
    with conn.cursor() as cur:
        cur.execute("DELETE FROM anomaly_contributors WHERE anomaly_id = %s", (anomaly_id,))
    
    # Insert new contributors
    with conn.cursor() as cur:
        for contrib in selected:
            cur.execute(
                """
                INSERT INTO anomaly_contributors (anomaly_id, label, amount, share_of_total)
                VALUES (%s, %s, %s, %s)
                """,
                (anomaly_id, contrib["label"], contrib["amount"], contrib["share_of_total"])
            )
        conn.commit()
    
    return len(selected)


def compute_contributors_for_company(
    conn: psycopg.Connection,
    company_id: UUID
) -> int:
    """
    Compute contributors for all anomalies of a company that don't have them yet.
    
    Args:
        conn: Database connection
        company_id: Company GUID
    
    Returns:
        int: Total number of contributors computed
    """
    # Find anomalies without contributors
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.id
            FROM anomalies a
            LEFT JOIN anomaly_contributors ac ON ac.anomaly_id = a.id
            WHERE a.company_id = %s AND ac.id IS NULL
            ORDER BY a.month DESC
            """,
            (str(company_id),)
        )
        anomaly_ids = [row[0] for row in cur.fetchall()]
    
    total = 0
    for anomaly_id in anomaly_ids:
        try:
            count = compute_contributors_for_anomaly(conn, anomaly_id)
            total += count
        except Exception as e:
            print(f"Error computing contributors for anomaly {anomaly_id}: {e}")
    
    print(f"Computed contributors for {len(anomaly_ids)} anomalies ({total} total)")
    return total


def get_contributors_for_anomaly(
    conn: psycopg.Connection,
    anomaly_id: int
) -> list[dict]:
    """
    Get contributors for an anomaly.
    
    Args:
        conn: Database connection
        anomaly_id: ID of the anomaly
    
    Returns:
        List of contributor dictionaries
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT label, amount, share_of_total
            FROM anomaly_contributors
            WHERE anomaly_id = %s
            ORDER BY ABS(amount) DESC
            """,
            (anomaly_id,)
        )
        return cur.fetchall()


def get_evidence_transactions(
    conn: psycopg.Connection,
    company_id: UUID,
    month: str,
    metric_name: str,
    limit: int = 10
) -> list[dict]:
    """
    Get sample transactions as evidence for an anomaly.
    
    Args:
        conn: Database connection
        company_id: Company GUID
        month: Month (YYYY-MM-DD format)
        metric_name: Name of the metric
        limit: Maximum number of transactions to return
    
    Returns:
        List of transaction dictionaries
    """
    try:
        filter_cond = metric_filter_condition(metric_name)
    except ValueError:
        return []
    
    query = f"""
        SELECT 
            tx_date, account_code, account_name,
            coa_code, coa_name, description,
            customer_name, amount
        FROM transactions
        WHERE company_id = %s 
          AND month = %s
          AND {filter_cond}
        ORDER BY ABS(amount) DESC
        LIMIT %s
    """
    
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, (str(company_id), month, limit))
        return cur.fetchall()
