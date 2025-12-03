# Finsmart ETL - AI CFO Backend

A YC-grade financial data pipeline that powers an AI CFO assistant.

**Reference:** https://docs.google.com/spreadsheets/d/1C1BHvJLBfU8UTEZYlHv08WRO6DZo49s2o0sPGG166xE/edit?gid=0#gid=0

## Overview

This backend service:

1. **Ingests** financial data from Finsmart API (Bronze layer)
2. **Normalizes** transactions into queryable format (Silver layer)
3. **Computes** monthly KPIs (Gold layer)
4. **Detects** anomalies when metrics change ≥20% month-over-month
5. **Explains** anomalies using OpenAI reasoning models
6. **Serves** CFO Month View with evidence for human verification

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Finsmart API   │────▶│   Raw Reports   │────▶│  Transactions   │
│  (External)     │     │   (Bronze)      │     │   (Silver)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   CFO View      │◀────│   Anomalies +   │◀────│  Monthly KPIs   │
│   (API/CLI)     │     │   Highlights    │     │   (Gold)        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL (running locally or remote)
- OpenAI API key

### 2. Installation

```bash
# Clone and navigate
cd finsmart

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=ozgurguler
DB_PASSWORD=

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_REASONING_MODEL=gpt-4o-mini

# Finsmart API
FINSMART_BASE_URL=https://dev-datauploadapi.finsmart.ai
API_KEY=your-finsmart-api-key
PASSWORD=your-finsmart-password
COMPANY_GUID=your-company-guid
```

### 4. Database Setup

```bash
# Run schema migrations
psql -f schema.sql
```

Or connect and run manually:

```bash
psql -h localhost -U ozgurguler -d postgres -f schema.sql
```

### 5. Test Database Connection

```bash
python -m finsmart_etl.runner ping
# Output: ok
```

## Usage

### Run Full ETL Pipeline

Fetch from Finsmart API, normalize, compute KPIs, detect anomalies:

```bash
python -m finsmart_etl.runner full-pipeline \
    --company-guid YOUR-COMPANY-GUID \
    --start 2022-01-01 \
    --end 2022-12-31
```

Add `--force-refresh` to re-fetch from API even if data exists.

### Load from Local File

For development/testing with existing `output.json`:

```bash
python -m finsmart_etl.runner load-file \
    --company-guid YOUR-COMPANY-GUID \
    --file output.json \
    --start 2022-01-01 \
    --end 2022-12-31
```

### View CFO Report

Generate CFO Month View for a specific month:

```bash
python -m finsmart_etl.runner cfo-view \
    --company-guid YOUR-COMPANY-GUID \
    --month 2022-09
```

Output is JSON with:
- `metrics_overview`: All KPIs with MoM changes
- `anomalies`: Flagged metrics with contributors, explanations, and evidence

### List Available Months

```bash
python -m finsmart_etl.runner list-months \
    --company-guid YOUR-COMPANY-GUID
```

## Project Structure

```
finsmart/
├── schema.sql              # PostgreSQL schema (Bronze/Silver/Gold)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── output.json             # Sample data (optional)
│
├── finsmart_etl/           # Main Python package
│   ├── __init__.py
│   ├── config.py           # Environment config loader
│   ├── db.py               # Database connection pool
│   ├── finsmart_client.py  # HTTP client for Finsmart API
│   ├── etl_raw.py          # Bronze: raw JSON ingestion
│   ├── etl_normalize.py    # Silver: transaction normalization
│   ├── metrics.py          # Gold: monthly KPI computation
│   ├── anomalies.py        # Anomaly detection (±20% MoM)
│   ├── contributors.py     # Root cause analysis
│   ├── explanations.py     # LLM explanation generation
│   ├── cfo_view.py         # CFO Month View builder
│   └── runner.py           # CLI entrypoints
│
└── tests/                  # Test suite
    ├── conftest.py         # Pytest fixtures
    ├── test_etl_normalize.py
    ├── test_metrics.py
    ├── test_anomalies.py
    ├── test_contributors.py
    ├── test_explanations.py
    └── test_cfo_view.py
```

## Database Schema

### Bronze Layer (Raw)
- `companies`: Company metadata
- `raw_reports`: Full JSON payloads from API

### Silver Layer (Normalized)
- `transactions`: Individual GL line items

### Gold Layer (Aggregated)
- `monthly_kpis`: Precomputed metrics per month
- `anomalies`: Flagged MoM changes ≥20%
- `anomaly_contributors`: Root cause vendors/customers
- `anomaly_highlights`: LLM-generated explanations (TR/EN)

## Idempotency

The ETL pipeline is fully idempotent:

1. **Raw ingestion**: Skips API call if `(company, period)` already exists
2. **Normalization**: Skips if transactions exist for the raw report
3. **KPIs/Anomalies**: Uses `ON CONFLICT DO UPDATE` for upserts

This means you can safely re-run the pipeline without duplicating data.

## Anomaly Detection

An anomaly is flagged when:
- **|MoM % change| ≥ 20%**

For each anomaly:
1. Top contributors (vendors/customers) are computed
2. LLM generates Turkish and English explanations
3. Evidence sample (raw transactions) is preserved

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=finsmart_etl

# Run specific test file
pytest tests/test_anomalies.py

# Run specific test
pytest tests/test_anomalies.py::TestAnomalyDetection::test_detect_anomalies
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `postgres` | Database name |
| `DB_USER` | `ozgurguler` | Database user |
| `DB_PASSWORD` | (empty) | Database password |
| `DB_POOL_SIZE` | `5` | Connection pool size |
| `OPENAI_API_KEY` | - | OpenAI API key (required for explanations) |
| `OPENAI_REASONING_MODEL` | `gpt-4o-mini` | Model for explanations |
| `FINSMART_BASE_URL` | `https://dev-datauploadapi.finsmart.ai` | API base URL |
| `API_KEY` | - | Finsmart API key |
| `PASSWORD` | - | Finsmart password |
| `COMPANY_GUID` | - | Default company GUID |

## Example Output: CFO Month View

```json
{
  "company": {
    "id": "abc-123",
    "name": "Finsmart Test Company",
    "business_model": "B2B SaaS"
  },
  "month": "2022-09-01",
  "month_label_tr": "Eylül 2022",
  "summary": {
    "total_metrics": 12,
    "total_anomalies": 2,
    "positive_anomalies": 1,
    "negative_anomalies": 1
  },
  "metrics_overview": [
    {
      "metric_name": "net_sales",
      "metric_name_tr": "net satışlar",
      "prev_value": 350000,
      "curr_value": 497000,
      "pct_change": 42.0,
      "is_anomalous": true
    }
  ],
  "anomalies": [
    {
      "metric_name": "advisory_expense",
      "prev_value": 82000,
      "curr_value": 272000,
      "pct_change": 231.7,
      "contributors": [
        {"label": "Atlas Graph", "amount": 96000, "share_pct": 35.3},
        {"label": "Ali Veli", "amount": 86000, "share_pct": 31.6}
      ],
      "highlights": {
        "tr": "Eylül ayında danışmanlık giderleri %232 artarak 82k TL'den 272k TL'ye yükselmiştir...",
        "en": "Advisory expenses increased by 232% from 82k TL to 272k TL in September..."
      },
      "evidence_sample": [
        {"date": "2022-09-15", "description": "Atlas Graph", "amount": 96000}
      ]
    }
  ]
}
```

## License

Private - Finsmart AI
