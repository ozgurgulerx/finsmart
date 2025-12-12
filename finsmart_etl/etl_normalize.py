"""
ETL Normalize Layer (Silver): Transform raw JSON to normalized transactions.

Handles:
- Parsing reportData from raw payloads
- Mapping JSON items to transaction rows
- Idempotent insertion into transactions table
"""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import psycopg
from psycopg.rows import dict_row


def has_transactions_for_report(conn: psycopg.Connection, raw_report_id: int) -> bool:
    """
    Check if transactions already exist for this raw report.
    
    Args:
        conn: Database connection
        raw_report_id: ID of the raw report
    
    Returns:
        bool: True if transactions exist, False otherwise
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT EXISTS(SELECT 1 FROM transactions WHERE source_report_id = %s)",
            (raw_report_id,)
        )
        return cur.fetchone()[0]


def map_report_item_to_tx_row(item: dict) -> dict:
    """
    Pure function mapping a single reportData JSON row to a transaction row dict.
    
    Args:
        item: Single item from reportData array
    
    Returns:
        dict with keys: tx_date, month, account_code, account_name, 
                       coa_code, coa_name, description, customer_name, amount
    """
    # Parse date - handle different formats
    date_str = item.get("receiptDate", "")
    if date_str:
        # Handle ISO format with time: "2022-01-01T00:00:00"
        if "T" in date_str:
            date_str = date_str.split("T")[0]
        tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        tx_date = date.today()
    
    # First of month for grouping
    month = tx_date.replace(day=1)
    
    # Extract fields with defaults
    account_code = item.get("accountCode", "")
    account_name = item.get("accountName", "")
    coa_code = item.get("code", "")
    coa_name = item.get("name", "")
    description = item.get("description", "")
    customer_name = item.get("customerName")
    
    # Amount - ensure it's a Decimal
    amount_raw = item.get("amount", 0)
    amount = Decimal(str(amount_raw)) if amount_raw else Decimal("0")
    
    return {
        "tx_date": tx_date,
        "month": month,
        "account_code": account_code,
        "account_name": account_name,
        "coa_code": coa_code,
        "coa_name": coa_name,
        "description": description,
        "customer_name": customer_name,
        "amount": amount,
    }


def normalize_raw_report(conn: psycopg.Connection, raw_report_id: int) -> int:
    """
    Normalize a raw report into transactions.
    
    Idempotent: if transactions already exist for this report, do nothing.
    
    Args:
        conn: Database connection
        raw_report_id: ID of the raw report to normalize
    
    Returns:
        int: Number of transactions inserted (0 if already processed)
    """
    # Check if already processed
    if has_transactions_for_report(conn, raw_report_id):
        print(f"Transactions already exist for report {raw_report_id}, skipping")
        return 0
    
    # Load raw payload
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT company_id, payload FROM raw_reports WHERE id = %s",
            (raw_report_id,)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Raw report {raw_report_id} not found")
        
        company_id = row["company_id"]
        payload = row["payload"]
    
    # Handle payload as string or dict
    if isinstance(payload, str):
        payload = json.loads(payload)
    
    # Extract reportData
    report_data = payload.get("data", {}).get("reportData", [])
    if not report_data:
        print(f"No reportData in raw report {raw_report_id}")
        # Mark as processed anyway
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE raw_reports SET status = 'processed' WHERE id = %s",
                (raw_report_id,)
            )
            conn.commit()
        return 0
    
    # Map and insert transactions
    rows_to_insert = []
    for item in report_data:
        tx_row = map_report_item_to_tx_row(item)
        rows_to_insert.append((
            str(company_id),
            tx_row["tx_date"],
            tx_row["month"],
            tx_row["account_code"],
            tx_row["account_name"],
            tx_row["coa_code"],
            tx_row["coa_name"],
            tx_row["description"],
            tx_row["customer_name"],
            tx_row["amount"],
            raw_report_id,
        ))
    
    # Batch insert
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO transactions (
                company_id, tx_date, month, account_code, account_name,
                coa_code, coa_name, description, customer_name, amount,
                source_report_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            rows_to_insert
        )
        
        # Update raw_reports status
        cur.execute(
            "UPDATE raw_reports SET status = 'processed' WHERE id = %s",
            (raw_report_id,)
        )
        conn.commit()
    
    print(f"Inserted {len(rows_to_insert)} transactions from report {raw_report_id}")
    return len(rows_to_insert)


def normalize_all_pending(conn: psycopg.Connection) -> int:
    """
    Normalize all pending raw reports.
    
    Args:
        conn: Database connection
    
    Returns:
        int: Total number of transactions inserted
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM raw_reports WHERE status = 'pending' ORDER BY id"
        )
        pending_ids = [row[0] for row in cur.fetchall()]
    
    total = 0
    for report_id in pending_ids:
        try:
            count = normalize_raw_report(conn, report_id)
            total += count
        except Exception as e:
            print(f"Error normalizing report {report_id}: {e}")
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE raw_reports SET status = 'error' WHERE id = %s",
                    (report_id,)
                )
                conn.commit()
    
    return total


def get_date_range_from_transactions(
    conn: psycopg.Connection, 
    company_id: UUID
) -> tuple[Optional[date], Optional[date]]:
    """
    Get the date range of transactions for a company.
    
    Args:
        conn: Database connection
        company_id: Company GUID
    
    Returns:
        Tuple of (min_date, max_date) or (None, None) if no transactions
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT MIN(tx_date), MAX(tx_date) 
            FROM transactions 
            WHERE company_id = %s
            """,
            (str(company_id),)
        )
        row = cur.fetchone()
        return (row[0], row[1]) if row else (None, None)
