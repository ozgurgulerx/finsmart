"""
Tests for CFO Month View.
"""

import pytest
from datetime import date
from decimal import Decimal


class TestCFOView:
    """Tests for CFO Month View functionality."""
    
    @pytest.fixture
    def setup_complete_data(self, db_conn, test_company_id):
        """Set up complete data for CFO view testing."""
        month = date(2022, 9, 1)
        prev_month = date(2022, 8, 1)
        
        # Create raw report
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO raw_reports (company_id, period_start, period_end, payload, status)
                VALUES (%s, %s, %s, '{}', 'processed')
                RETURNING id
                """,
                (str(test_company_id), date(2022, 1, 1), date(2022, 12, 31))
            )
            raw_report_id = cur.fetchone()[0]
        
        # Insert KPIs for both months
        kpis = [
            (test_company_id, prev_month, "net_sales", Decimal("100000")),
            (test_company_id, month, "net_sales", Decimal("150000")),
            (test_company_id, prev_month, "advisory_expense", Decimal("30000")),
            (test_company_id, month, "advisory_expense", Decimal("80000")),
        ]
        
        with db_conn.cursor() as cur:
            for kpi in kpis:
                cur.execute(
                    """
                    INSERT INTO monthly_kpis (company_id, month, metric_name, value)
                    VALUES (%s, %s, %s, %s)
                    """,
                    kpi
                )
        
        # Create anomaly
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO anomalies 
                (company_id, month, metric_name, prev_value, curr_value, pct_change, severity_score)
                VALUES (%s, %s, 'advisory_expense', 30000, 80000, 166.67, 166.67)
                RETURNING id
                """,
                (str(test_company_id), month)
            )
            anomaly_id = cur.fetchone()[0]
        
        # Add contributor
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO anomaly_contributors (anomaly_id, label, amount, share_of_total)
                VALUES (%s, 'Consultant X', 50000, 0.625),
                       (%s, 'Consultant Y', 30000, 0.375)
                """,
                (anomaly_id, anomaly_id)
            )
        
        # Add highlight
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO anomaly_highlights (anomaly_id, language, text)
                VALUES (%s, 'tr', 'Eylül ayında danışmanlık giderleri %167 arttı.'),
                       (%s, 'en', 'Advisory expenses increased by 167% in September.')
                """,
                (anomaly_id, anomaly_id)
            )
        
        # Insert transactions
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions 
                (company_id, tx_date, month, account_code, account_name,
                 coa_code, coa_name, description, customer_name, amount, source_report_id)
                VALUES 
                (%s, %s, %s, '2.5.2', 'Advisory', '760.01', 'DANISMANLIK', 
                 'Consultant X', NULL, 50000, %s),
                (%s, %s, %s, '2.5.2', 'Advisory', '760.01', 'DANISMANLIK',
                 'Consultant Y', NULL, 30000, %s)
                """,
                (str(test_company_id), date(2022, 9, 15), month, raw_report_id,
                 str(test_company_id), date(2022, 9, 20), month, raw_report_id)
            )
        
        return {
            "company_id": test_company_id,
            "month": month,
            "anomaly_id": anomaly_id,
        }
    
    def test_get_metrics_overview(self, db_conn, setup_complete_data):
        """Test metrics overview retrieval."""
        from finsmart_etl.cfo_view import get_metrics_overview
        
        data = setup_complete_data
        metrics = get_metrics_overview(db_conn, data["company_id"], data["month"])
        
        assert len(metrics) >= 2
        
        # Find net_sales
        net_sales = next((m for m in metrics if m["metric_name"] == "net_sales"), None)
        assert net_sales is not None
        assert net_sales["prev_value"] == 100000.0
        assert net_sales["curr_value"] == 150000.0
        assert net_sales["pct_change"] == 50.0  # (150-100)/100 * 100
        
        # Find advisory_expense - should be flagged as anomalous
        advisory = next((m for m in metrics if m["metric_name"] == "advisory_expense"), None)
        assert advisory is not None
        assert advisory["is_anomalous"] is True
    
    def test_get_anomaly_details(self, db_conn, setup_complete_data):
        """Test anomaly details retrieval."""
        from finsmart_etl.cfo_view import get_anomaly_details
        
        data = setup_complete_data
        anomalies = get_anomaly_details(
            db_conn, data["company_id"], data["month"],
            generate_missing_highlights=False
        )
        
        assert len(anomalies) == 1
        
        anomaly = anomalies[0]
        assert anomaly["metric_name"] == "advisory_expense"
        assert anomaly["pct_change"] > 100
        
        # Check contributors
        assert len(anomaly["contributors"]) == 2
        assert anomaly["contributors"][0]["label"] == "Consultant X"
        
        # Check highlights
        assert anomaly["highlights"]["tr"] != ""
        assert anomaly["highlights"]["en"] != ""
        
        # Check evidence
        assert len(anomaly["evidence_sample"]) >= 1
    
    def test_build_cfo_month_view(self, db_conn, setup_complete_data):
        """Test complete CFO view building."""
        from finsmart_etl.cfo_view import build_cfo_month_view
        
        data = setup_complete_data
        
        view = build_cfo_month_view(
            db_conn, data["company_id"], data["month"],
            ensure_computed=False,  # Data already set up
            generate_highlights=False
        )
        
        # Check structure
        assert "company" in view
        assert "month" in view
        assert "month_label_tr" in view
        assert "summary" in view
        assert "metrics_overview" in view
        assert "anomalies" in view
        
        # Check company info
        assert view["company"]["name"] == "Test Company"
        
        # Check month label
        assert "Eylül" in view["month_label_tr"]
        
        # Check summary
        assert view["summary"]["total_anomalies"] == 1
        
        # Check metrics
        assert len(view["metrics_overview"]) >= 2
        
        # Check anomalies
        assert len(view["anomalies"]) == 1
        assert view["anomalies"][0]["metric_name"] == "advisory_expense"
    
    def test_cfo_view_includes_evidence(self, db_conn, setup_complete_data):
        """Test that CFO view includes transaction evidence."""
        from finsmart_etl.cfo_view import build_cfo_month_view
        
        data = setup_complete_data
        
        view = build_cfo_month_view(
            db_conn, data["company_id"], data["month"],
            ensure_computed=False,
            generate_highlights=False
        )
        
        anomaly = view["anomalies"][0]
        evidence = anomaly["evidence_sample"]
        
        assert len(evidence) >= 1
        
        # Check evidence structure
        sample = evidence[0]
        assert "date" in sample
        assert "account_name" in sample
        assert "description" in sample
        assert "amount" in sample
        assert "amount_formatted" in sample


class TestAvailableMonths:
    """Tests for available months query."""
    
    def test_get_available_months(self, db_conn, test_company_id):
        """Test getting available months for a company."""
        from finsmart_etl.cfo_view import get_available_months
        
        # Insert some KPIs
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO monthly_kpis (company_id, month, metric_name, value)
                VALUES 
                (%s, '2022-07-01', 'net_sales', 100000),
                (%s, '2022-08-01', 'net_sales', 110000),
                (%s, '2022-09-01', 'net_sales', 120000)
                """,
                (str(test_company_id), str(test_company_id), str(test_company_id))
            )
        
        months = get_available_months(db_conn, test_company_id)
        
        assert len(months) == 3
        # Should be ordered descending
        assert "2022-09" in months[0]
        assert "2022-08" in months[1]
        assert "2022-07" in months[2]
