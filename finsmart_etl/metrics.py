"""
Metrics Computation (Gold Layer): Compute monthly KPIs from transactions.

Defines metric definitions and computes aggregated KPIs per month.
"""

import json
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

import psycopg


@dataclass
class MetricDefinition:
    """Definition of a KPI metric."""
    name: str
    description: str
    sql_filter: str  # SQL WHERE clause fragment
    is_revenue: bool = False  # True if this is a revenue metric


# Metric definitions - easily extensible
METRIC_DEFINITIONS: list[MetricDefinition] = [
    # Revenue metrics (account_code starts with 1.*)
    MetricDefinition(
        name="net_sales",
        description="Net Sales (Local + Global)",
        sql_filter="account_code LIKE '1.1%%'",
        is_revenue=True,
    ),
    MetricDefinition(
        name="local_sales",
        description="Local Sales",
        sql_filter="account_name = 'Local Sales'",
        is_revenue=True,
    ),
    MetricDefinition(
        name="global_sales",
        description="Global Sales",
        sql_filter="account_name = 'Global Sales'",
        is_revenue=True,
    ),
    MetricDefinition(
        name="returns",
        description="Sales Returns",
        sql_filter="account_name = 'Returns (-)'",
        is_revenue=True,
    ),
    
    # Expense metrics (account_code starts with 2.*)
    MetricDefinition(
        name="advisory_expense",
        description="Advisory/Consulting Expenses",
        sql_filter="(account_name = 'Advisory' OR coa_name ILIKE '%%DANISMAN%%')",
    ),
    MetricDefinition(
        name="software_expense",
        description="Software Expenses",
        sql_filter="account_name = 'Software'",
    ),
    MetricDefinition(
        name="payroll",
        description="Payroll/Personnel Expenses",
        sql_filter="(account_name = 'Payroll' OR account_name ILIKE '%%Personnel%%')",
    ),
    MetricDefinition(
        name="marketing",
        description="Marketing Expenses",
        sql_filter="account_name = 'Marketing'",
    ),
    MetricDefinition(
        name="hospitality",
        description="Hospitality/Entertainment",
        sql_filter="account_name = 'Hospitality'",
    ),
    MetricDefinition(
        name="office_rent",
        description="Office Rent",
        sql_filter="account_name = 'Office Rent'",
    ),
    MetricDefinition(
        name="car_expenses",
        description="Car/Vehicle Expenses",
        sql_filter="account_name = 'Car Expenses'",
    ),
    MetricDefinition(
        name="food_expenses",
        description="Food Expenses",
        sql_filter="account_name = 'Food Expenses'",
    ),
    MetricDefinition(
        name="travel_expenses",
        description="Travel Expenses",
        sql_filter="account_name = 'Travel'",
    ),
    
    # Interest/Financial
    MetricDefinition(
        name="interest_income",
        description="Interest Income",
        sql_filter="account_name = 'Commision & Interest Income'",
        is_revenue=True,
    ),
]


def get_metric_definition(metric_name: str) -> Optional[MetricDefinition]:
    """
    Get metric definition by name.
    
    Args:
        metric_name: Name of the metric
    
    Returns:
        MetricDefinition or None if not found
    """
    for m in METRIC_DEFINITIONS:
        if m.name == metric_name:
            return m
    return None


def compute_single_metric(
    conn: psycopg.Connection,
    company_id: UUID,
    metric: MetricDefinition
) -> int:
    """
    Compute a single metric for all months and upsert into monthly_kpis.
    
    Args:
        conn: Database connection
        company_id: Company GUID
        metric: Metric definition to compute
    
    Returns:
        int: Number of rows upserted
    """
    query = f"""
        INSERT INTO monthly_kpis (company_id, month, metric_name, value, meta)
        SELECT
            company_id,
            month,
            %s AS metric_name,
            COALESCE(SUM(amount), 0) AS value,
            %s::jsonb AS meta
        FROM transactions
        WHERE company_id = %s
          AND {metric.sql_filter}
        GROUP BY company_id, month
        ON CONFLICT (company_id, month, metric_name) 
        DO UPDATE SET 
            value = EXCLUDED.value,
            meta = EXCLUDED.meta
        RETURNING id
    """
    
    meta = {
        "description": metric.description,
        "sql_filter": metric.sql_filter,
        "is_revenue": metric.is_revenue,
    }
    
    with conn.cursor() as cur:
        cur.execute(query, (metric.name, json.dumps(meta), str(company_id)))
        rows = cur.fetchall()
        conn.commit()
        return len(rows)


def compute_monthly_kpis(conn: psycopg.Connection, company_id: UUID) -> dict[str, int]:
    """
    Compute all monthly KPIs for a company.
    
    Args:
        conn: Database connection
        company_id: Company GUID
    
    Returns:
        dict: Metric name -> number of rows upserted
    """
    results = {}
    for metric in METRIC_DEFINITIONS:
        count = compute_single_metric(conn, company_id, metric)
        results[metric.name] = count
        if count > 0:
            print(f"  Computed {metric.name}: {count} months")
    
    return results


def compute_total_revenue(conn: psycopg.Connection, company_id: UUID) -> int:
    """
    Compute total revenue (sum of revenue metrics) per month.
    
    Args:
        conn: Database connection
        company_id: Company GUID
    
    Returns:
        int: Number of rows upserted
    """
    # Get all revenue metric names
    revenue_metrics = [m.name for m in METRIC_DEFINITIONS if m.is_revenue and m.name != "returns"]
    if not revenue_metrics:
        return 0
    
    placeholders = ", ".join(["%s"] * len(revenue_metrics))
    
    query = f"""
        INSERT INTO monthly_kpis (company_id, month, metric_name, value)
        SELECT
            company_id,
            month,
            'total_revenue' AS metric_name,
            COALESCE(SUM(value), 0) AS value
        FROM monthly_kpis
        WHERE company_id = %s
          AND metric_name IN ({placeholders})
        GROUP BY company_id, month
        ON CONFLICT (company_id, month, metric_name)
        DO UPDATE SET value = EXCLUDED.value
        RETURNING id
    """
    
    with conn.cursor() as cur:
        cur.execute(query, (str(company_id), *revenue_metrics))
        rows = cur.fetchall()
        conn.commit()
        return len(rows)


def compute_total_expenses(conn: psycopg.Connection, company_id: UUID) -> int:
    """
    Compute total expenses (sum of expense metrics) per month.
    
    Args:
        conn: Database connection
        company_id: Company GUID
    
    Returns:
        int: Number of rows upserted
    """
    # Get all expense metric names
    expense_metrics = [m.name for m in METRIC_DEFINITIONS if not m.is_revenue]
    if not expense_metrics:
        return 0
    
    placeholders = ", ".join(["%s"] * len(expense_metrics))
    
    query = f"""
        INSERT INTO monthly_kpis (company_id, month, metric_name, value)
        SELECT
            company_id,
            month,
            'total_expenses' AS metric_name,
            COALESCE(SUM(value), 0) AS value
        FROM monthly_kpis
        WHERE company_id = %s
          AND metric_name IN ({placeholders})
        GROUP BY company_id, month
        ON CONFLICT (company_id, month, metric_name)
        DO UPDATE SET value = EXCLUDED.value
        RETURNING id
    """
    
    with conn.cursor() as cur:
        cur.execute(query, (str(company_id), *expense_metrics))
        rows = cur.fetchall()
        conn.commit()
        return len(rows)


def get_kpis_for_month(
    conn: psycopg.Connection,
    company_id: UUID,
    month: str  # YYYY-MM-DD format (first of month)
) -> list[dict]:
    """
    Get all KPIs for a specific month.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        month: Month as string (YYYY-MM-DD, first of month)
    
    Returns:
        List of KPI dictionaries
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT metric_name, value, meta
            FROM monthly_kpis
            WHERE company_id = %s AND month = %s
            ORDER BY metric_name
            """,
            (str(company_id), month)
        )
        return [
            {"metric_name": row[0], "value": float(row[1]), "meta": row[2]}
            for row in cur.fetchall()
        ]
