"""
Tests for ETL normalization layer.
"""

import pytest
from datetime import date
from decimal import Decimal

from finsmart_etl.etl_normalize import (
    map_report_item_to_tx_row,
    has_transactions_for_report,
)


class TestMapReportItem:
    """Tests for map_report_item_to_tx_row function."""
    
    def test_basic_mapping(self):
        """Test basic field mapping."""
        item = {
            "accountCode": "2.5.2",
            "accountName": "Advisory",
            "code": "760.01.01",
            "name": "DANISMANLIK GIDERLERI",
            "description": "Consultant X",
            "receiptDate": "2022-09-15T00:00:00",
            "amount": 50000.0,
            "customerName": None
        }
        
        result = map_report_item_to_tx_row(item)
        
        assert result["tx_date"] == date(2022, 9, 15)
        assert result["month"] == date(2022, 9, 1)
        assert result["account_code"] == "2.5.2"
        assert result["account_name"] == "Advisory"
        assert result["coa_code"] == "760.01.01"
        assert result["coa_name"] == "DANISMANLIK GIDERLERI"
        assert result["description"] == "Consultant X"
        assert result["customer_name"] is None
        assert result["amount"] == Decimal("50000.0")
    
    def test_with_customer_name(self):
        """Test mapping with customer name."""
        item = {
            "accountCode": "1.1.1",
            "accountName": "Local Sales",
            "code": "600.1.18",
            "name": "SALES",
            "description": "Invoice 123",
            "receiptDate": "2022-09-20T00:00:00",
            "amount": 100000.0,
            "customerName": "Acme Corp"
        }
        
        result = map_report_item_to_tx_row(item)
        
        assert result["customer_name"] == "Acme Corp"
        assert result["account_name"] == "Local Sales"
    
    def test_month_boundary(self):
        """Test that month is correctly set to first of month."""
        item = {
            "accountCode": "1.1.1",
            "accountName": "Sales",
            "code": "600",
            "name": "Sales",
            "description": "Test",
            "receiptDate": "2022-12-31T00:00:00",
            "amount": 1000.0,
            "customerName": None
        }
        
        result = map_report_item_to_tx_row(item)
        
        assert result["tx_date"] == date(2022, 12, 31)
        assert result["month"] == date(2022, 12, 1)
    
    def test_missing_fields(self):
        """Test handling of missing fields."""
        item = {
            "receiptDate": "2022-09-15T00:00:00",
            "amount": 1000.0,
        }
        
        result = map_report_item_to_tx_row(item)
        
        assert result["account_code"] == ""
        assert result["account_name"] == ""
        assert result["description"] == ""
        assert result["amount"] == Decimal("1000.0")
    
    def test_zero_amount(self):
        """Test handling of zero amount."""
        item = {
            "accountCode": "1.1.1",
            "accountName": "Sales",
            "code": "600",
            "name": "Sales",
            "description": "Test",
            "receiptDate": "2022-09-15T00:00:00",
            "amount": 0,
            "customerName": None
        }
        
        result = map_report_item_to_tx_row(item)
        
        assert result["amount"] == Decimal("0")
    
    def test_negative_amount(self):
        """Test handling of negative amount (returns/credits)."""
        item = {
            "accountCode": "1.2.1",
            "accountName": "Returns (-)",
            "code": "610",
            "name": "Returns",
            "description": "Refund",
            "receiptDate": "2022-09-15T00:00:00",
            "amount": -5000.0,
            "customerName": "Customer X"
        }
        
        result = map_report_item_to_tx_row(item)
        
        assert result["amount"] == Decimal("-5000.0")
