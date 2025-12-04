#!/usr/bin/env python3
"""
CLI Runner: Orchestration entrypoints for the ETL pipeline.

Commands:
- full-pipeline: Run complete ETL for a company/period
- cfo-view: Display CFO month view
- load-file: Load data from local JSON file
"""

import argparse
import json
import sys
from datetime import date, datetime
from uuid import UUID

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .config import get_config
from .db import get_conn, ping, close_pool
from .finsmart_client import FinsmartClient
from .etl_raw import get_or_create_company, ensure_raw_report, load_from_file
from .etl_normalize import normalize_raw_report, normalize_all_pending
from .metrics import compute_monthly_kpis
from .anomalies import detect_anomalies
from .contributors import compute_contributors_for_company
from .explanations import generate_highlights_for_new_anomalies
from .cfo_view import build_cfo_month_view, get_company_by_guid, get_available_months


def run_full_pipeline_for_company_period(
    company_guid: str,
    period_start: date,
    period_end: date,
    force_refresh: bool = False,
) -> dict:
    """
    Run the complete ETL pipeline for a company and period.
    
    Steps:
    1. Ensure company exists
    2. Fetch/ensure raw report (idempotent)
    3. Normalize transactions (idempotent)
    4. Compute monthly KPIs
    5. Detect anomalies
    6. Compute contributors
    7. Generate highlights
    
    Args:
        company_guid: Finsmart company GUID
        period_start: Period start date
        period_end: Period end date
        force_refresh: If True, re-fetch from API even if data exists
    
    Returns:
        dict: Pipeline execution summary
    """
    config = get_config()
    
    print(f"=" * 60)
    print(f"Running full pipeline for company {company_guid}")
    print(f"Period: {period_start} to {period_end}")
    print(f"Force refresh: {force_refresh}")
    print(f"=" * 60)
    
    with get_conn() as conn:
        # Step 1: Ensure company exists
        print("\n[1/7] Ensuring company exists...")
        company_id = get_or_create_company(conn, company_guid)
        print(f"Company ID: {company_id}")
        
        # Step 2: Fetch/ensure raw report
        print("\n[2/7] Fetching raw report (idempotent)...")
        client = FinsmartClient(
            config.finsmart_base_url,
            config.finsmart_api_key,
            config.finsmart_password
        )
        raw_report_id = ensure_raw_report(
            conn, client, company_id, company_guid,
            period_start, period_end, force_refresh
        )
        
        # Step 3: Normalize transactions
        print("\n[3/7] Normalizing transactions (idempotent)...")
        tx_count = normalize_raw_report(conn, raw_report_id)
        
        # Step 4: Compute KPIs
        print("\n[4/7] Computing monthly KPIs...")
        kpi_results = compute_monthly_kpis(conn, company_id)
        
        # Step 5: Detect anomalies
        print("\n[5/7] Detecting anomalies (±20% threshold)...")
        anomaly_count = detect_anomalies(conn, company_id)
        
        # Step 6: Compute contributors
        print("\n[6/7] Computing anomaly contributors...")
        contributor_count = compute_contributors_for_company(conn, company_id)
        
        # Step 7: Generate highlights
        print("\n[7/7] Generating LLM highlights...")
        highlight_count = generate_highlights_for_new_anomalies(conn, company_id)
        
        print("\n" + "=" * 60)
        print("Pipeline complete!")
        print(f"=" * 60)
        
        return {
            "company_id": str(company_id),
            "company_guid": company_guid,
            "raw_report_id": raw_report_id,
            "transactions_inserted": tx_count,
            "kpi_metrics": len(kpi_results),
            "anomalies_detected": anomaly_count,
            "contributors_computed": contributor_count,
            "highlights_generated": highlight_count,
        }


def run_load_from_file(
    company_guid: str,
    filepath: str,
    period_start: date,
    period_end: date,
) -> dict:
    """
    Load data from a local JSON file instead of API.
    
    Useful for development and testing.
    
    Args:
        company_guid: Finsmart company GUID
        filepath: Path to JSON file
        period_start: Period start date
        period_end: Period end date
    
    Returns:
        dict: Pipeline execution summary
    """
    print(f"=" * 60)
    print(f"Loading from file: {filepath}")
    print(f"Company GUID: {company_guid}")
    print(f"=" * 60)
    
    with get_conn() as conn:
        # Ensure company exists
        print("\n[1/6] Ensuring company exists...")
        company_id = get_or_create_company(conn, company_guid)
        print(f"Company ID: {company_id}")
        
        # Load from file
        print("\n[2/6] Loading raw report from file...")
        raw_report_id = load_from_file(conn, company_id, period_start, period_end, filepath)
        
        # Normalize
        print("\n[3/6] Normalizing transactions...")
        tx_count = normalize_raw_report(conn, raw_report_id)
        
        # Compute KPIs
        print("\n[4/6] Computing monthly KPIs...")
        compute_monthly_kpis(conn, company_id)
        
        # Detect anomalies
        print("\n[5/6] Detecting anomalies...")
        anomaly_count = detect_anomalies(conn, company_id)
        
        # Compute contributors
        print("\n[6/6] Computing contributors...")
        compute_contributors_for_company(conn, company_id)
        
        print("\n" + "=" * 60)
        print("Load complete!")
        print(f"=" * 60)
        
        return {
            "company_id": str(company_id),
            "raw_report_id": raw_report_id,
            "transactions_inserted": tx_count,
            "anomalies_detected": anomaly_count,
        }


def print_cfo_month_view_cli(
    company_guid: str,
    month_str: str,
    generate_highlights: bool = True,
    skip_compute: bool = False,
    output_dir: str = None,
) -> None:
    """
    Print CFO month view to stdout as JSON and save reports.
    
    Args:
        company_guid: Finsmart company GUID
        month_str: Month string (YYYY-MM or YYYY-MM-DD)
        generate_highlights: Generate LLM highlights
        skip_compute: Skip recomputing KPIs/anomalies
        output_dir: Directory to save report files (optional)
    """
    from .cfo_view import format_report_markdown, save_reports_to_files
    
    # Parse month
    if len(month_str) == 7:  # YYYY-MM
        month = datetime.strptime(month_str + "-01", "%Y-%m-%d").date()
    else:  # YYYY-MM-DD
        month = datetime.strptime(month_str, "%Y-%m-%d").date()
    month = month.replace(day=1)
    month_short = month.strftime("%Y-%m")
    
    with get_conn() as conn:
        # Find company
        company = get_company_by_guid(conn, company_guid)
        if not company:
            print(f"Error: Company with GUID {company_guid} not found", file=sys.stderr)
            sys.exit(1)
        
        company_id = company["id"]
        company_name = company["name"]
        
        # Build CFO view
        view = build_cfo_month_view(
            conn, company_id, month,
            ensure_computed=not skip_compute,
            generate_highlights=generate_highlights
        )
        
        # Display Markdown reports if executive_report exists
        exec_report = view.get("executive_report")
        if exec_report:
            print("\n" + "="*80, file=sys.stderr)
            print("TÜRKÇE RAPOR", file=sys.stderr)
            print("="*80, file=sys.stderr)
            print(format_report_markdown(exec_report, "tr"), file=sys.stderr)
            
            print("\n" + "="*80, file=sys.stderr)
            print("ENGLISH REPORT", file=sys.stderr)
            print("="*80, file=sys.stderr)
            print(format_report_markdown(exec_report, "en"), file=sys.stderr)
            
            # Save to files if output_dir specified
            if output_dir:
                files = save_reports_to_files(
                    exec_report, company_name, month_short, output_dir
                )
                print(f"\n[CFO View] Reports saved:", file=sys.stderr)
                print(f"  - Turkish: {files['tr']}", file=sys.stderr)
                print(f"  - English: {files['en']}", file=sys.stderr)
        
        # Print JSON to stdout
        print(json.dumps(view, indent=2, ensure_ascii=False, default=str))


def list_available_months_cli(company_guid: str) -> None:
    """
    List available months for a company.
    
    Args:
        company_guid: Finsmart company GUID
    """
    with get_conn() as conn:
        company = get_company_by_guid(conn, company_guid)
        if not company:
            print(f"Error: Company with GUID {company_guid} not found", file=sys.stderr)
            sys.exit(1)
        
        months = get_available_months(conn, company["id"])
        
        print(f"Available months for {company['name']}:")
        for m in months:
            print(f"  {m}")


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Finsmart ETL - AI CFO Backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python -m finsmart_etl.runner full-pipeline --company-guid YOUR-GUID --start 2022-01-01 --end 2022-12-31

  # Load from local file
  python -m finsmart_etl.runner load-file --company-guid YOUR-GUID --file output.json --start 2022-01-01 --end 2022-12-31

  # View CFO report for a month
  python -m finsmart_etl.runner cfo-view --company-guid YOUR-GUID --month 2022-09

  # List available months
  python -m finsmart_etl.runner list-months --company-guid YOUR-GUID

  # Test database connection
  python -m finsmart_etl.runner ping
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # full-pipeline command
    pipeline_parser = subparsers.add_parser("full-pipeline", help="Run complete ETL pipeline")
    pipeline_parser.add_argument("--company-guid", required=True, help="Finsmart company GUID")
    pipeline_parser.add_argument("--start", required=True, help="Period start date (YYYY-MM-DD)")
    pipeline_parser.add_argument("--end", required=True, help="Period end date (YYYY-MM-DD)")
    pipeline_parser.add_argument("--force-refresh", action="store_true", help="Force re-fetch from API")
    
    # load-file command
    load_parser = subparsers.add_parser("load-file", help="Load data from local JSON file")
    load_parser.add_argument("--company-guid", required=True, help="Finsmart company GUID")
    load_parser.add_argument("--file", required=True, help="Path to JSON file")
    load_parser.add_argument("--start", required=True, help="Period start date (YYYY-MM-DD)")
    load_parser.add_argument("--end", required=True, help="Period end date (YYYY-MM-DD)")
    
    # cfo-view command
    view_parser = subparsers.add_parser("cfo-view", help="Display CFO month view")
    view_parser.add_argument("--company-guid", required=True, help="Finsmart company GUID")
    view_parser.add_argument("--month", required=True, help="Month (YYYY-MM or YYYY-MM-DD)")
    view_parser.add_argument("--no-highlights", action="store_true", help="Skip LLM highlight generation")
    view_parser.add_argument("--skip-compute", action="store_true", help="Skip recomputing KPIs/anomalies, just fetch existing")
    view_parser.add_argument("--output-dir", help="Directory to save report files (TR and EN markdown)")
    
    # list-months command
    months_parser = subparsers.add_parser("list-months", help="List available months")
    months_parser.add_argument("--company-guid", required=True, help="Finsmart company GUID")
    
    # ping command
    subparsers.add_parser("ping", help="Test database connection")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "ping":
            if ping():
                print("ok")
                sys.exit(0)
            else:
                print("failed")
                sys.exit(1)
        
        elif args.command == "full-pipeline":
            result = run_full_pipeline_for_company_period(
                company_guid=args.company_guid,
                period_start=datetime.strptime(args.start, "%Y-%m-%d").date(),
                period_end=datetime.strptime(args.end, "%Y-%m-%d").date(),
                force_refresh=args.force_refresh,
            )
            print("\nSummary:")
            print(json.dumps(result, indent=2))
        
        elif args.command == "load-file":
            result = run_load_from_file(
                company_guid=args.company_guid,
                filepath=args.file,
                period_start=datetime.strptime(args.start, "%Y-%m-%d").date(),
                period_end=datetime.strptime(args.end, "%Y-%m-%d").date(),
            )
            print("\nSummary:")
            print(json.dumps(result, indent=2))
        
        elif args.command == "cfo-view":
            print_cfo_month_view_cli(
                company_guid=args.company_guid,
                month_str=args.month,
                generate_highlights=not args.no_highlights,
                skip_compute=args.skip_compute,
                output_dir=args.output_dir,
            )
        
        elif args.command == "list-months":
            list_available_months_cli(args.company_guid)
    
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        close_pool()


if __name__ == "__main__":
    main()
