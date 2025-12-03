"""
Tests for anomaly contributors computation.
"""

import pytest
from datetime import date
from decimal import Decimal

from finsmart_etl.contributors import (
    metric_filter_condition,
    get_contributors_for_anomaly,
)


class TestMetricFilterCondition:
    """Tests for metric filter condition mapping."""
    
    def test_net_sales_filter(self):
        """Test net_sales filter condition."""
        cond = metric_filter_condition("net_sales")
        assert "1.1" in cond or "account_code" in cond
    
    def test_advisory_expense_filter(self):
        """Test advisory_expense filter condition."""
        cond = metric_filter_condition("advisory_expense")
        assert "Advisory" in cond or "DANISMAN" in cond
    
    def test_unknown_metric_fallback(self):
        """Test fallback for unknown metrics."""
        cond = metric_filter_condition("some_custom_metric")
        assert "some_custom_metric" in cond


class TestContributorsComputation:
    """Integration tests for contributors computation."""
    
    @pytest.fixture
    def setup_anomaly_with_transactions(self, db_conn, test_company_id):
        """Set up an anomaly with related transactions."""
        month = date(2022, 9, 1)
        
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
        
        # Insert transactions
        transactions = [
            ("Advisory", "Consultant Alpha", Decimal("50000")),
            ("Advisory", "Consultant Beta", Decimal("30000")),
            ("Advisory", "Consultant Gamma", Decimal("15000")),
            ("Advisory", "Consultant Delta", Decimal("5000")),
        ]
        
        with db_conn.cursor() as cur:
            for account_name, description, amount in transactions:
                cur.execute(
                    """
                    INSERT INTO transactions 
                    (company_id, tx_date, month, account_code, account_name,
                     coa_code, coa_name, description, customer_name, amount, source_report_id)
                    VALUES (%s, %s, %s, '2.5.2', %s, '760.01', 'DANISMANLIK', %s, NULL, %s, %s)
                    """,
                    (str(test_company_id), date(2022, 9, 15), month, 
                     account_name, description, amount, raw_report_id)
                )
        
        # Create anomaly
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO anomalies 
                (company_id, month, metric_name, prev_value, curr_value, pct_change, severity_score)
                VALUES (%s, %s, 'advisory_expense', 30000, 100000, 233.33, 233.33)
                RETURNING id
                """,
                (str(test_company_id), month)
            )
            anomaly_id = cur.fetchone()[0]
        
        return {
            "company_id": test_company_id,
            "anomaly_id": anomaly_id,
            "month": month,
        }
    
    def test_compute_contributors(self, db_conn, setup_anomaly_with_transactions):
        """Test that contributors are computed correctly."""
        from finsmart_etl.contributors import compute_contributors_for_anomaly
        
        data = setup_anomaly_with_transactions
        count = compute_contributors_for_anomaly(db_conn, data["anomaly_id"])
        
        assert count > 0
        
        # Fetch contributors
        contributors = get_contributors_for_anomaly(db_conn, data["anomaly_id"])
        
        assert len(contributors) > 0
        
        # Top contributor should be Consultant Alpha (50000)
        top = contributors[0]
        assert "Alpha" in top["label"]
        assert float(top["amount"]) == 50000.0
    
    def test_contributors_share_sums_correctly(self, db_conn, setup_anomaly_with_transactions):
        """Test that share_of_total values are reasonable."""
        from finsmart_etl.contributors import compute_contributors_for_anomaly
        
        data = setup_anomaly_with_transactions
        compute_contributors_for_anomaly(db_conn, data["anomaly_id"])
        
        contributors = get_contributors_for_anomaly(db_conn, data["anomaly_id"])
        
        total_share = sum(float(c["share_of_total"]) for c in contributors)
        
        # Should cover significant portion of total
        assert total_share >= 0.8 or len(contributors) <= 3
    
    def test_contributors_ordered_by_amount(self, db_conn, setup_anomaly_with_transactions):
        """Test that contributors are ordered by amount descending."""
        from finsmart_etl.contributors import compute_contributors_for_anomaly
        
        data = setup_anomaly_with_transactions
        compute_contributors_for_anomaly(db_conn, data["anomaly_id"])
        
        contributors = get_contributors_for_anomaly(db_conn, data["anomaly_id"])
        
        amounts = [abs(float(c["amount"])) for c in contributors]
        assert amounts == sorted(amounts, reverse=True)
