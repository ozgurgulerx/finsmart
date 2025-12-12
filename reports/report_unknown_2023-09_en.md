# September 2023 Financial Anomaly Summary Report

---

## Executive Overview

September 2023 shows mixed signals: modest overall net sales growth but material shifts in revenue composition and concentrated, volatile expense items. Several metrics reflect one-off large receipts or payments and repeated same‑day entries, indicating potential booking, timing or data quality issues that warrant immediate review.

## Detected Anomalies

### 1. hospitality

**Change:** 7.9% increase

**Why Anomaly?**
> Flagged due to an enormous YoY change (~+13,530%) and a large deviation from the 3-month rolling average (~+106%), with a near-threshold Z-score; classified as 'yoy_and_rolling'.

**Root Cause Analysis:**
> In September 2023 hospitality rose from 225,215.43 to 243,106.77. The increase is mainly driven by a 123,556.06 '2023/EYLUL UCRET BORDROSU' item (50.8% share) and 91,376.36 payments to 'SET KURUMSAL HIZMETLER TIC.A.S.' (37.6% share).

### 2. interest_income

**Change:** -1.1% decrease

**Why Anomaly?**
> Flagged because YoY growth is extreme (+2,482%) and the current value is ~140.8% above the 3-month rolling average; the combination triggered a 'yoy_and_rolling' alert despite a near-zero Z-score.

**Root Cause Analysis:**
> Interest income for September 2023 is 33,267.0 TL, down from 33,625.44 TL. The decline is primarily driven by timing and volume variations in N KOLAY BONO SATIS %36 FAIZ ORANI transactions and partial recording/distribution changes.

### 3. car_expenses

**Change:** 73.1% increase

**Why Anomaly?**
> Flagged because YoY change is very large (+510%) and the 3-month rolling average deviation is ~55%; combined signals labeled this as 'yoy_and_rolling'.

**Root Cause Analysis:**
> Car expenses rose from 24,449.9 to 42,334.04. The main driver is OTOKOC OTOMOTIV TIC.A.S. (10,879.91, ~51.4% share), with contributions from EDENRED KURUMSAL COZUMLER A.S. and FULLJET AKARYAKIT LTD.STI.; evidence includes two 10,000 payments to OTOKOC on 2023-09-01.

### 4. net_sales

**Change:** 3.3% increase

**Why Anomaly?**
> Flagged primarily for a very large year‑over‑year surge (+236.8%), while other signals remained within normal ranges ('yoy' driven).

**Root Cause Analysis:**
> Net sales increased from 4,255,403.38 to 4,396,574.88, driven by large receipts from customers such as Future Finance Group (825,130.81), Bright Future Finance (402,690.69) and True North Finance (400,000.0). Duplicate entries for some customers in evidence may indicate booking/recording anomalies.

### 5. local_sales

**Change:** -15.2% decrease

**Why Anomaly?**
> Flagged due to an unusual YoY swing (large percentage deviation vs same month last year), with other metrics normal; classified as 'yoy'.

**Root Cause Analysis:**
> Domestic sales fell from 4,090,113.18 to 3,466,997.0. The decline is driven by high concentration in three customers (Future Finance Group 825,130.81, Bright Future Finance 402,690.69, True North Finance 400,000.0) and repeated entries in evidence suggesting invoicing/timing or data quality issues.

### 6. office_rent

**Change:** 21.3% increase

**Why Anomaly?**
> Flagged mainly due to an extreme YoY spike (office rent rose ~166.9% vs prior year), hence labeled 'yoy'.

**Root Cause Analysis:**
> Office rent rose from 38,100.0 to 46,233.1, primarily driven by a one-off 19,000.0 payment to AC YAPI INS. SAN.VE TIC.A.S., which accounts for 82.2% of the increase. Duplicate-looking entries and smaller TEKNOPARK ISTANBUL charges also contributed.

### 7. global_sales

**Change:** 79.4% increase

**Why Anomaly?**
> Flagged because of a large YoY increase (+140%) combined with a substantial deviation from the 3-month rolling average (current value ~54.9% below the rolling average); conflicting signals resulted in 'yoy_and_rolling'.

**Root Cause Analysis:**
> Global sales rose from 165,290.2 to 296,535.88, driven primarily by a 108,008.0 contribution from Pixel Perfect Software (72.8%) and 40,259.94 from Clearview Finance (27.2%). Evidence shows duplicate same‑day large transactions, indicating concentration in a few large or batch invoices.

### 8. software_expense

**Change:** -94.8% decrease

**Why Anomaly?**
> Flagged due to an extreme month‑to‑month drop and ~-99.4% deviation from the 3‑month rolling average; classified as 'rolling'.

**Root Cause Analysis:**
> Software expense fell from 80,147.1 to 4,133.3. The decline reflects the absence of prior-period one-off large software charges; current month expenses are concentrated in OPENAL, LLC payments totaling 2,066.65.

### 9. returns

**Change:** -92.6% decrease

**Why Anomaly?**
> Flagged because current returns are ~81% below the 3‑month rolling average, triggering the 'rolling' signal.

**Root Cause Analysis:**
> Returns fell from 779,170 to 57,442. The primary causes are the absence of large prior-period returns and concentration of current returns in a single customer, Future Finance Group (two entries totaling 57,442).

### 10. advisory_expense

**Change:** 49.0% increase

**Why Anomaly?**
> Flagged because the current value is ~77% above the 3‑month rolling average; detected as a 'rolling' anomaly.

**Root Cause Analysis:**
> Advisory expense increased from 216,306.06 to 322,221.34, primarily driven by a large payment to BEAN HR YONETIM LTD.STI. (72,700.0, ~45.1%) and additional payments to GORKEM CETIN (44,465.22) and TOKEN FINANSAL TEKNOLOJILER (38,945.45).

### 11. food_expenses

**Change:** 524.1% increase

**Why Anomaly?**
> Flagged because both YoY change and rolling-average deviation exceeded thresholds, resulting in a 'yoy_and_rolling' alert.

**Root Cause Analysis:**
> Food expenses rose from 3,345.46 to 20,877.48. The increase is driven by multiple large supplier payments on the same date and duplicate entries (e.g., ZORLU YATIRIM A.S. and OLUSUM REST.LTD.STI.), concentrating the expense.

---

## Recommended Actions

- Reconcile large one-off receipts and payments to source invoices and bank records; correct any duplicate or batched postings.
- Audit high-concentration customers for billing timing, duplicate entries and refund/credit patterns; implement customer-level monitoring thresholds.
- Investigate same‑date duplicate large transactions (both sales and purchases) and remove/adjust erroneous duplicate postings.
- Require supporting approvals and contract references for significant payments (rent, advisory, hospitality, vehicle) before posting.
- Standardize revenue recognition and interest booking policies to eliminate timing-driven volatility in interest income.
- Review return processes and historical causes for large prior-period returns; implement controls to validate and approve refunds.
- Document one-off software and vendor spend and normalize monthly budgets for comparability; require CAPEX/OPEX classification review.
- Implement automated ERP validation rules and alerts for identical date/amount/vendor or customer combinations to prevent duplicate entries.

---

*This report was generated automatically.*