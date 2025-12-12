"""
ETL Raw Layer (Bronze): Idempotent ingestion of raw JSON payloads.

Handles:
- Checking for existing reports
- Fetching from Finsmart API
- Storing raw payloads in raw_reports table
"""

import json
from datetime import date
from typing import Optional
from uuid import UUID

import psycopg

from .finsmart_client import FinsmartClient


def get_or_create_company(
    conn: psycopg.Connection,
    finsmart_guid: str,
    name: str = "Unknown",
    business_model: Optional[str] = None
) -> UUID:
    """
    Get existing company or create new one.
    
    Args:
        conn: Database connection
        finsmart_guid: Finsmart company GUID
        name: Company name
        business_model: Business model description
    
    Returns:
        UUID: Company GUID (primary key)
    """
    with conn.cursor() as cur:
        # Try to find existing by Finsmart GUID
        cur.execute(
            "SELECT finsmart_guid FROM companies WHERE finsmart_guid = %s",
            (finsmart_guid,)
        )
        row = cur.fetchone()
        if row:
            return row[0]
        
        # Create new using Finsmart GUID as the primary key
        cur.execute(
            """
            INSERT INTO companies (finsmart_guid, name, business_model)
            VALUES (%s, %s, %s)
            RETURNING finsmart_guid
            """,
            (finsmart_guid, name, business_model)
        )
        conn.commit()
        return cur.fetchone()[0]


def get_existing_raw_report_id(
    conn: psycopg.Connection,
    company_id: UUID,
    period_start: date,
    period_end: date,
) -> Optional[int]:
    """
    Check if a raw report already exists for this company-period.
    
    Args:
        conn: Database connection
        company_id: Company GUID
        period_start: Report period start date
        period_end: Report period end date
    
    Returns:
        int or None: Existing raw_reports.id if found, else None
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id FROM raw_reports
            WHERE company_id = %s 
              AND period_start = %s 
              AND period_end = %s
            """,
            (str(company_id), period_start, period_end)
        )
        row = cur.fetchone()
        return row[0] if row else None


def ingest_report(
    conn: psycopg.Connection,
    company_id: UUID,
    period_start: date,
    period_end: date,
    payload: dict,
) -> int:
    """
    Insert a new raw report into the database.
    
    Args:
        conn: Database connection
        company_id: Company GUID
        period_start: Report period start date
        period_end: Report period end date
        payload: Raw JSON payload from Finsmart API
    
    Returns:
        int: New raw_reports.id
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_reports (company_id, period_start, period_end, payload, status)
            VALUES (%s, %s, %s, %s, 'pending')
            RETURNING id
            """,
            (str(company_id), period_start, period_end, json.dumps(payload))
        )
        conn.commit()
        return cur.fetchone()[0]


def ensure_raw_report(
    conn: psycopg.Connection,
    finsmart_client: FinsmartClient,
    company_id: UUID,
    company_guid: str,
    period_start: date,
    period_end: date,
    force_refresh: bool = False,
) -> int:
    """
    Idempotent ETL entrypoint for raw data ingestion.
    
    - If a raw report exists for (company, period) and force_refresh=False, return its id.
    - Otherwise, fetch from Finsmart API and insert.
    
    Args:
        conn: Database connection
        finsmart_client: Finsmart API client
        company_id: Internal company UUID
        company_guid: Finsmart company GUID
        period_start: Report period start date
        period_end: Report period end date
        force_refresh: If True, re-fetch even if data exists
    
    Returns:
        int: raw_reports.id (existing or newly created)
    """
    # Check for existing report
    if not force_refresh:
        existing_id = get_existing_raw_report_id(conn, company_id, period_start, period_end)
        if existing_id is not None:
            print(f"Raw report already exists (id={existing_id}), skipping API call")
            return existing_id
    
    # Fetch from Finsmart API
    print(f"Fetching data from Finsmart API for company {company_guid}...")
    payload = finsmart_client.fetch_company_data(company_guid)
    
    # Extract company info if available
    company_info = payload.get("data", {}).get("companyInfo", {})
    if company_info:
        # Update company name if we have it
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE companies 
                SET name = COALESCE(NULLIF(%s, ''), name),
                    business_model = COALESCE(NULLIF(%s, ''), business_model)
                WHERE id = %s
                """,
                (
                    company_info.get("companyName", ""),
                    company_info.get("businessModelName", ""),
                    str(company_id)
                )
            )
            conn.commit()
    
    # Handle force_refresh: delete existing before insert
    if force_refresh:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM raw_reports 
                WHERE company_id = %s AND period_start = %s AND period_end = %s
                """,
                (str(company_id), period_start, period_end)
            )
            conn.commit()
    
    # Insert new report
    try:
        report_id = ingest_report(conn, company_id, period_start, period_end, payload)
        print(f"Ingested raw report (id={report_id})")
        return report_id
        
    except psycopg.errors.UniqueViolation:
        # Race condition: another process inserted, fetch existing
        conn.rollback()
        existing_id = get_existing_raw_report_id(conn, company_id, period_start, period_end)
        if existing_id:
            print(f"Report inserted by concurrent process (id={existing_id})")
            return existing_id
        raise


def load_from_file(
    conn: psycopg.Connection,
    company_id: UUID,
    period_start: date,
    period_end: date,
    filepath: str,
) -> int:
    """
    Load raw report from a local JSON file (useful for testing/dev).
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        period_start: Report period start date
        period_end: Report period end date
        filepath: Path to JSON file
    
    Returns:
        int: raw_reports.id
    """
    # Check existing
    existing_id = get_existing_raw_report_id(conn, company_id, period_start, period_end)
    if existing_id is not None:
        print(f"Raw report already exists (id={existing_id})")
        return existing_id
    
    # Load from file
    with open(filepath, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    return ingest_report(conn, company_id, period_start, period_end, payload)
