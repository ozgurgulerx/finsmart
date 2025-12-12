-- =============================================================================
-- AI CFO Backend - PostgreSQL Schema
-- Bronze / Silver / Gold Architecture
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------------
-- BRONZE LAYER: Raw Data
-- -----------------------------------------------------------------------------

-- Companies (tenants)
CREATE TABLE IF NOT EXISTS companies (
    -- Use external Finsmart GUID as the *only* identifier
    finsmart_guid  UUID PRIMARY KEY,
    name           TEXT NOT NULL,
    business_model TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Raw JSON payloads (append-only audit trail)
CREATE TABLE IF NOT EXISTS raw_reports (
    id           BIGSERIAL PRIMARY KEY,
    company_id   UUID NOT NULL REFERENCES companies(finsmart_guid),
    period_start DATE NOT NULL,
    period_end   DATE NOT NULL,
    payload      JSONB NOT NULL,
    ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    status       TEXT NOT NULL DEFAULT 'pending'  -- 'pending' | 'processed' | 'error'
);

-- Ensure one raw report per company-period (idempotent ETL)
ALTER TABLE raw_reports
DROP CONSTRAINT IF EXISTS raw_reports_company_period_uniq;

ALTER TABLE raw_reports
ADD CONSTRAINT raw_reports_company_period_uniq
UNIQUE (company_id, period_start, period_end);

-- -----------------------------------------------------------------------------
-- SILVER LAYER: Normalized Transactions
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS transactions (
    id              BIGSERIAL PRIMARY KEY,
    company_id      UUID NOT NULL REFERENCES companies(finsmart_guid),
    tx_date         DATE NOT NULL,
    month           DATE NOT NULL,  -- first of month (e.g. 2025-09-01)
    account_code    TEXT NOT NULL,  -- e.g. '2.5.2'
    account_name    TEXT NOT NULL,  -- e.g. 'Advisory'
    coa_code        TEXT,
    coa_name        TEXT,
    description     TEXT,
    customer_name   TEXT,
    amount          NUMERIC(18,2) NOT NULL,
    source_report_id BIGINT NOT NULL REFERENCES raw_reports(id)
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_transactions_company_month
    ON transactions (company_id, month);

CREATE INDEX IF NOT EXISTS idx_transactions_company_account_month
    ON transactions (company_id, account_code, month);

CREATE INDEX IF NOT EXISTS idx_transactions_source_report
    ON transactions (source_report_id);

-- -----------------------------------------------------------------------------
-- GOLD LAYER: KPIs, Anomalies, Contributors, Explanations
-- -----------------------------------------------------------------------------

-- Monthly KPIs (precomputed metrics)
CREATE TABLE IF NOT EXISTS monthly_kpis (
    id          BIGSERIAL PRIMARY KEY,
    company_id  UUID NOT NULL REFERENCES companies(finsmart_guid),
    month       DATE NOT NULL,
    metric_name TEXT NOT NULL,         -- 'net_sales', 'advisory_expense', etc.
    value       NUMERIC(18,2) NOT NULL,
    meta        JSONB,
    UNIQUE (company_id, month, metric_name)
);

CREATE INDEX IF NOT EXISTS idx_monthly_kpis_company_month
    ON monthly_kpis (company_id, month);

-- Detected anomalies (smart detection: YoY + Rolling Avg + Z-Score)
CREATE TABLE IF NOT EXISTS anomalies (
    id             BIGSERIAL PRIMARY KEY,
    company_id     UUID NOT NULL REFERENCES companies(finsmart_guid),
    month          DATE NOT NULL,
    metric_name    TEXT NOT NULL,
    prev_value     NUMERIC(18,2),
    curr_value     NUMERIC(18,2) NOT NULL,
    pct_change     NUMERIC,                 -- MoM: (curr - prev) / prev * 100
    severity_score NUMERIC,                 -- Composite score from detection signals
    status         TEXT NOT NULL DEFAULT 'open',  -- 'open', 'muted', 'confirmed'
    meta           JSONB,                   -- Detection details: yoy_pct, rolling_pct, zscore, reason
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (company_id, month, metric_name)
);

CREATE INDEX IF NOT EXISTS idx_anomalies_company_month
    ON anomalies (company_id, month);

-- Root-cause contributors for each anomaly
CREATE TABLE IF NOT EXISTS anomaly_contributors (
    id             BIGSERIAL PRIMARY KEY,
    anomaly_id     BIGINT NOT NULL REFERENCES anomalies(id) ON DELETE CASCADE,
    label          TEXT NOT NULL,          -- vendor/customer/description
    amount         NUMERIC(18,2) NOT NULL,
    share_of_total NUMERIC NOT NULL        -- 0..1
);

CREATE INDEX IF NOT EXISTS idx_anomaly_contributors_anomaly
    ON anomaly_contributors (anomaly_id);

-- LLM-generated explanations (TR/EN)
CREATE TABLE IF NOT EXISTS anomaly_highlights (
    id          BIGSERIAL PRIMARY KEY,
    anomaly_id  BIGINT NOT NULL REFERENCES anomalies(id) ON DELETE CASCADE,
    language    TEXT NOT NULL,             -- 'tr' or 'en'
    text        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (anomaly_id, language)
);

CREATE INDEX IF NOT EXISTS idx_anomaly_highlights_anomaly
    ON anomaly_highlights (anomaly_id);

-- -----------------------------------------------------------------------------
-- VIEWS (optional convenience)
-- -----------------------------------------------------------------------------

-- View: Anomalies with their highlights
CREATE OR REPLACE VIEW v_anomalies_with_highlights AS
SELECT 
    a.*,
    h_tr.text AS highlight_tr,
    h_en.text AS highlight_en
FROM anomalies a
LEFT JOIN anomaly_highlights h_tr ON h_tr.anomaly_id = a.id AND h_tr.language = 'tr'
LEFT JOIN anomaly_highlights h_en ON h_en.anomaly_id = a.id AND h_en.language = 'en';

-- View: Monthly KPIs with MoM change
CREATE OR REPLACE VIEW v_monthly_kpis_with_change AS
SELECT 
    k.*,
    LAG(k.value) OVER (PARTITION BY k.company_id, k.metric_name ORDER BY k.month) AS prev_value,
    CASE 
        WHEN LAG(k.value) OVER (PARTITION BY k.company_id, k.metric_name ORDER BY k.month) IS NULL 
             OR LAG(k.value) OVER (PARTITION BY k.company_id, k.metric_name ORDER BY k.month) = 0 
        THEN NULL
        ELSE (k.value - LAG(k.value) OVER (PARTITION BY k.company_id, k.metric_name ORDER BY k.month)) 
             / LAG(k.value) OVER (PARTITION BY k.company_id, k.metric_name ORDER BY k.month) * 100
    END AS pct_change
FROM monthly_kpis k;
