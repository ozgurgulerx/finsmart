"""
Tests for LLM explanations.
"""

import pytest
from datetime import date
from decimal import Decimal

from finsmart_etl.explanations import (
    month_label_tr,
    metric_name_tr,
    format_amount_tr,
    build_prompt,
)


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_month_label_tr(self):
        """Test Turkish month label generation."""
        assert month_label_tr(date(2022, 9, 1)) == "Eylül 2022"
        assert month_label_tr(date(2022, 1, 15)) == "Ocak 2022"
        assert month_label_tr(date(2023, 12, 31)) == "Aralık 2023"
    
    def test_metric_name_tr(self):
        """Test Turkish metric name translation."""
        assert metric_name_tr("net_sales") == "net satışlar"
        assert metric_name_tr("advisory_expense") == "danışmanlık giderleri"
        assert metric_name_tr("unknown_metric") == "unknown_metric"
    
    def test_format_amount_tr_thousands(self):
        """Test amount formatting for thousands."""
        assert format_amount_tr(50000) == "50k TL"
        assert format_amount_tr(82000) == "82k TL"
        assert format_amount_tr(1500) == "2k TL"  # Rounds
    
    def test_format_amount_tr_millions(self):
        """Test amount formatting for millions."""
        assert format_amount_tr(1500000) == "1.5M TL"
        assert format_amount_tr(2000000) == "2.0M TL"
    
    def test_format_amount_tr_small(self):
        """Test amount formatting for small amounts."""
        assert format_amount_tr(500) == "500 TL"
        assert format_amount_tr(0) == "0 TL"
    
    def test_format_amount_tr_negative(self):
        """Test amount formatting for negative amounts."""
        assert format_amount_tr(-50000) == "50k TL"  # Uses absolute value


class TestPromptBuilding:
    """Tests for prompt building."""
    
    def test_build_prompt_structure(self):
        """Test that prompt has required structure."""
        payload = {
            "company": {"name": "Test Co", "business_model": "B2B SaaS"},
            "anomaly": {
                "metric_name": "advisory_expense",
                "metric_name_tr": "danışmanlık giderleri",
                "month": "2022-09-01",
                "month_label_tr": "Eylül 2022",
                "prev_value": 30000,
                "curr_value": 80000,
                "pct_change": 166.67,
            },
            "contributors": [
                {"label": "Consultant X", "amount": 50000, "amount_formatted": "50k TL", "share_pct": 62.5},
            ],
        }
        
        prompt = build_prompt(payload)
        
        # Should contain key elements
        assert "finansal" in prompt.lower() or "financial" in prompt.lower()
        assert "JSON" in prompt
        assert "tr_explanation" in prompt
        assert "en_explanation" in prompt
        assert "Test Co" in prompt or "advisory" in prompt
    
    def test_build_prompt_includes_data(self):
        """Test that prompt includes the actual data."""
        payload = {
            "company": {"name": "Acme Corp", "business_model": "SaaS"},
            "anomaly": {
                "metric_name": "net_sales",
                "metric_name_tr": "net satışlar",
                "month": "2022-10-01",
                "month_label_tr": "Ekim 2022",
                "prev_value": 100000,
                "curr_value": 150000,
                "pct_change": 50.0,
            },
            "contributors": [],
        }
        
        prompt = build_prompt(payload)
        
        # Should include the metric name
        assert "net_sales" in prompt or "satış" in prompt.lower()


class TestLLMIntegration:
    """Tests for LLM integration (mocked)."""
    
    @pytest.fixture
    def setup_anomaly_for_highlight(self, db_conn, test_company_id):
        """Set up complete anomaly data for highlight generation."""
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
        with db_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions 
                (company_id, tx_date, month, account_code, account_name,
                 coa_code, coa_name, description, customer_name, amount, source_report_id)
                VALUES (%s, %s, %s, '2.5.2', 'Advisory', '760.01', 'DANISMANLIK', 
                        'Consultant X', NULL, 80000, %s)
                """,
                (str(test_company_id), date(2022, 9, 15), month, raw_report_id)
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
                VALUES (%s, 'Consultant X', 80000, 1.0)
                """,
                (anomaly_id,)
            )
        
        return {"company_id": test_company_id, "anomaly_id": anomaly_id}
    
    def test_generate_highlight_with_mock_llm(self, db_conn, setup_anomaly_for_highlight):
        """Test highlight generation with mocked LLM."""
        from finsmart_etl.explanations import generate_highlight_for_anomaly
        
        data = setup_anomaly_for_highlight
        
        # Mock LLM function
        def mock_llm(prompt):
            return {
                "tr_explanation": "Test Türkçe açıklama",
                "en_explanation": "Test English explanation",
            }
        
        result = generate_highlight_for_anomaly(db_conn, data["anomaly_id"], llm_func=mock_llm)
        
        assert result is True
        
        # Verify highlights were stored
        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT language, text FROM anomaly_highlights WHERE anomaly_id = %s",
                (data["anomaly_id"],)
            )
            highlights = {row[0]: row[1] for row in cur.fetchall()}
        
        assert "tr" in highlights
        assert "en" in highlights
        assert "Türkçe" in highlights["tr"]
