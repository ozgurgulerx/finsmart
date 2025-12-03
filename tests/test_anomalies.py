"""
Tests for anomaly detection.
"""

import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4


class TestAnomalyDetection:
    """Tests for anomaly detection logic."""
    
    @pytest.fixture
    def setup_kpis(self, db_conn, test_company_id):
        """Insert test KPIs for anomaly detection."""
        kpis = [
            # net_sales: stable (should not trigger)
            (test_company_id, date(2022, 7, 1), "net_sales", Decimal("100000")),
            (test_company_id, date(2022, 8, 1), "net_sales", Decimal("105000")),  # +5%
            (test_company_id, date(2022, 9, 1), "net_sales", Decimal("110000")),  # +4.8%
            
            # advisory_expense: big jump (should trigger)
            (test_company_id, date(2022, 7, 1), "advisory_expense", Decimal("30000")),
            (test_company_id, date(2022, 8, 1), "advisory_expense", Decimal("32000")),  # +6.7%
            (test_company_id, date(2022, 9, 1), "advisory_expense", Decimal("80000")),  # +150% -> ANOMALY
            
            # marketing: moderate change (borderline)
            (test_company_id, date(2022, 7, 1), "marketing", Decimal("10000")),
            (test_company_id, date(2022, 8, 1), "marketing", Decimal("12500")),  # +25% -> ANOMALY
            (test_company_id, date(2022, 9, 1), "marketing", Decimal("11000")),  # -12%
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
        
        return test_company_id
    
    def test_detect_anomalies(self, db_conn, setup_kpis):
        """Test anomaly detection with ±20% threshold."""
        from finsmart_etl.anomalies import detect_anomalies
        
        company_id = setup_kpis
        count = detect_anomalies(db_conn, company_id, threshold_pct=20.0)
        
        # Should detect at least the advisory_expense jump
        assert count >= 1
        
        # Verify advisory_expense anomaly exists
        with db_conn.cursor() as cur:
            cur.execute(
                """
                SELECT metric_name, pct_change, severity_score
                FROM anomalies
                WHERE company_id = %s AND month = %s AND metric_name = 'advisory_expense'
                """,
                (str(company_id), date(2022, 9, 1))
            )
            row = cur.fetchone()
        
        assert row is not None
        metric_name, pct_change, severity = row
        assert pct_change > 100  # Should be ~150%
        assert severity > 100
    
    def test_no_false_positives(self, db_conn, setup_kpis):
        """Test that stable metrics don't trigger anomalies."""
        from finsmart_etl.anomalies import detect_anomalies
        
        company_id = setup_kpis
        detect_anomalies(db_conn, company_id, threshold_pct=20.0)
        
        # net_sales should NOT have anomaly in September
        with db_conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM anomalies
                WHERE company_id = %s AND month = %s AND metric_name = 'net_sales'
                """,
                (str(company_id), date(2022, 9, 1))
            )
            row = cur.fetchone()
        
        assert row is None, "Stable metric should not trigger anomaly"
    
    def test_anomaly_threshold_customization(self, db_conn, setup_kpis):
        """Test that threshold can be customized."""
        from finsmart_etl.anomalies import detect_anomalies
        
        company_id = setup_kpis
        
        # With 50% threshold, fewer anomalies
        count_50 = detect_anomalies(db_conn, company_id, threshold_pct=50.0)
        
        # Clear and re-detect with 10% threshold
        with db_conn.cursor() as cur:
            cur.execute("DELETE FROM anomalies WHERE company_id = %s", (str(company_id),))
        
        count_10 = detect_anomalies(db_conn, company_id, threshold_pct=10.0)
        
        # Lower threshold should catch more anomalies
        assert count_10 >= count_50


class TestAnomalyQueries:
    """Tests for anomaly query functions."""
    
    @pytest.fixture
    def setup_anomalies(self, db_conn, test_company_id):
        """Insert test anomalies."""
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO anomalies 
                (company_id, month, metric_name, prev_value, curr_value, pct_change, severity_score, status)
                VALUES 
                (%s, %s, 'advisory_expense', 30000, 80000, 166.67, 166.67, 'open'),
                (%s, %s, 'marketing', 10000, 12500, 25.0, 25.0, 'open')
                """,
                (str(test_company_id), date(2022, 9, 1),
                 str(test_company_id), date(2022, 8, 1))
            )
        
        return test_company_id
    
    def test_get_anomalies_for_month(self, db_conn, setup_anomalies):
        """Test fetching anomalies for a specific month."""
        from finsmart_etl.anomalies import get_anomalies_for_month
        
        company_id = setup_anomalies
        anomalies = get_anomalies_for_month(db_conn, company_id, str(date(2022, 9, 1)))
        
        assert len(anomalies) == 1
        assert anomalies[0]["metric_name"] == "advisory_expense"
    
    def test_get_anomalies_ordered_by_severity(self, db_conn, setup_anomalies):
        """Test that anomalies are ordered by severity."""
        from finsmart_etl.anomalies import get_anomalies_for_company
        
        company_id = setup_anomalies
        anomalies = get_anomalies_for_company(db_conn, company_id)
        
        assert len(anomalies) >= 2
        # Should be ordered by severity descending
        severities = [a["severity_score"] for a in anomalies]
        assert severities == sorted(severities, reverse=True)
