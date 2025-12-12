"""
Pytest fixtures for Finsmart ETL tests.
"""

import os
import pytest
import psycopg
from uuid import uuid4

# Set test environment variables before importing modules
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "postgres")
os.environ.setdefault("DB_USER", "ozgurguler")
os.environ.setdefault("DB_PASSWORD", "")
os.environ.setdefault("OPENAI_API_KEY", "test-key")


@pytest.fixture(scope="session")
def db_dsn():
    """Database DSN for tests."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "postgres")
    user = os.getenv("DB_USER", "ozgurguler")
    password = os.getenv("DB_PASSWORD", "")
    
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    return f"postgresql://{user}@{host}:{port}/{name}"


@pytest.fixture(scope="function")
def db_conn(db_dsn):
    """
    Database connection fixture.
    
    Each test gets its own connection that is rolled back after the test.
    """
    conn = psycopg.connect(db_dsn)
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture(scope="function")
def test_company_id(db_conn):
    """Create a test company and return its ID."""
    company_guid = str(uuid4())
    with db_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO companies (finsmart_guid, name, business_model)
            VALUES (%s, 'Test Company', 'B2B SaaS')
            RETURNING finsmart_guid
            """,
            (company_guid,)
        )
        company_id = cur.fetchone()[0]
    return company_id


@pytest.fixture
def sample_report_data():
    """Sample reportData for testing."""
    return [
        {
            "accountCode": "1.1.1",
            "accountName": "Local Sales",
            "code": "600.1.18",
            "name": "SALES REVENUE",
            "description": "Customer A",
            "receiptDate": "2022-09-15T00:00:00",
            "amount": 100000.0,
            "customerName": "Customer A"
        },
        {
            "accountCode": "1.1.1",
            "accountName": "Local Sales",
            "code": "600.1.18",
            "name": "SALES REVENUE",
            "description": "Customer B",
            "receiptDate": "2022-09-20T00:00:00",
            "amount": 50000.0,
            "customerName": "Customer B"
        },
        {
            "accountCode": "2.5.2",
            "accountName": "Advisory",
            "code": "760.01.01",
            "name": "DANISMANLIK GIDERLERI",
            "description": "Consultant X",
            "receiptDate": "2022-09-10T00:00:00",
            "amount": 80000.0,
            "customerName": None
        },
        {
            "accountCode": "2.5.2",
            "accountName": "Advisory",
            "code": "760.01.01",
            "name": "DANISMANLIK GIDERLERI",
            "description": "Consultant Y",
            "receiptDate": "2022-09-25T00:00:00",
            "amount": 45000.0,
            "customerName": None
        },
    ]


@pytest.fixture
def sample_payload(sample_report_data):
    """Sample API payload for testing."""
    return {
        "data": {
            "companyInfo": {
                "companyName": "Test Company",
                "companyDesciption": "A test company",
                "businessModelName": "B2B SaaS"
            },
            "reportData": sample_report_data
        },
        "isSuccess": True,
        "statusCode": 200
    }
