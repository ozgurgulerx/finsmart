# September 2023 Financial Anomaly Summary Report

---

## Executive Overview

September 2023 shows notable volatility in several accounts driven by large one-off receipts/payments and concentrated customer activity. Revenue spikes are often tied to few large customers, while expense anomalies are frequently caused by single high-value payments or potential duplicate postings. Overall, data-quality checks and segregation of one-off versus recurring items are required.

## Detected Anomalies

### 1. hospitality

**Change:** 7.9% increase

**Why Anomaly?**
> Current value showed an inconceivable year-over-year jump and a large deviation from the 3-month rolling average (~106.5%), so the combination of YoY and rolling signals triggered the anomaly.

**Root Cause Analysis:**
> In September 2023 hospitality rose from 225,215.43 to 243,106.77 (+7.94%). The increase is mainly driven by the 123,556.06 '2023/EYLUL UCRET BORDROSU' item (50.8% share) and 91,376.36 payments to 'SET KURUMSAL HIZMETLER TIC.A.S.' (37.6% share).

### 2. interest_income

**Change:** 1.1% decrease

**Why Anomaly?**
> Extreme YoY change (driven by a very low prior-period value) and a large deviation from the 3-month rolling average (~140.8%) caused the YoY and rolling signals to flag this metric.

**Root Cause Analysis:**
> Interest income for September 2023 is 33,267.0 TL, down from 33,625.44 TL (-1.07%). The decline is primarily driven by timing and volume variations in N KOLAY BONO SATIS %36 FAIZ ORANI transactions (7,404.13; 4,598.35; 2,564.39 TL) and slight recording/distribution differences.

### 3. car_expenses

**Change:** 73.1% increase

**Why Anomaly?**
> A large YoY surge (~510%) combined with a significant deviation from the 3-month rolling average (~55%) triggered the anomaly detection.

**Root Cause Analysis:**
> Car expenses rose from 24,449.90 to 42,334.04 (+73.15%). Main driver is OTOKOC OTOMOTIV TIC.A.S. (10,879.91 TL, ~51.4%), with additional contributions from EDENRED KURUMSAL COZUMLER A.S. (3,033.01) and FULLJET AKARYAKIT LTD.STI. (3,024.01). Evidence includes two 10,000 payments to OTOKOC on 2023-09-01.

### 4. net_sales

**Change:** 3.3% increase

**Why Anomaly?**
> Flagged primarily due to an extreme year-over-year surge (net sales jumped ~237% vs prior year); rolling and z-score were within thresholds so YoY drove the detection.

**Root Cause Analysis:**
> Net sales increased from 4,255,403.38 to 4,396,574.88 (+3.32%) driven by large receipts. Major contributors include Future Finance Group 825,130.81; Bright Future Finance 402,690.69; True North Finance 400,000.00. Duplicate entries for Bright Future and True North in evidence may indicate booking/recording anomalies.

### 5. local_sales

**Change:** 15.2% decrease

**Why Anomaly?**
> Flagged because YoY change was an extreme spike compared with prior year (beyond ±30% threshold); rolling and z-score were normal, so YoY drove the alert.

**Root Cause Analysis:**
> Domestic sales fell from 4,090,113.18 to 3,466,997.00 (-15.23%). Main drivers are high concentration in three customers (Future Finance Group 825,130.81; Bright Future Finance 402,690.69; True North Finance 400,000.00) and repeated entries in evidence suggesting invoicing/timing or data quality issues.

### 6. office_rent

**Change:** 21.3% increase

**Why Anomaly?**
> Detected mainly due to a very large YoY change (~166.9%), exceeding the ±30% threshold; other signals were within normal bands.

**Root Cause Analysis:**
> Office rent rose from 38,100.0 to 46,233.1 (+21.35%). The primary cause is a one-off 19,000.0 payment to AC YAPI INS. SAN.VE TIC.A.S. (accounting for ~82.2% of the change). Smaller TEKNOPARK ISTANBUL charges and duplicate-seeming entries also contributed.

### 7. global_sales

**Change:** 79.4% increase

**Why Anomaly?**
> Current value jumped ~140% YoY and simultaneously deviated substantially from the 3-month rolling average (~-54.9%); both YoY and rolling signals triggered the anomaly.

**Root Cause Analysis:**
> Global sales rose from 165,290.20 to 296,535.88 (+79.40%), driven primarily by a 108,008.0 contribution from Pixel Perfect Software (72.8%) and 40,259.94 from Clearview Finance (27.2%). Evidence shows duplicate same-day large transactions; the increase is concentrated in few large, likely one-off or batch invoices.

### 8. software_expense

**Change:** 94.8% decrease

**Why Anomaly?**
> A massive month-over-month drop and extreme deviation from the 3-month rolling average (~-99.4%) triggered the rolling signal for anomaly.

**Root Cause Analysis:**
> Software expense fell from 80,147.10 to 4,133.30 (-94.84%). The decline is mainly due to the absence of prior-period one-off large software charges; current month expenses are limited and concentrated in OPENAL, LLC payments totaling ~2,066.65 TL, with duplicated smaller transactions in evidence.

### 9. returns

**Change:** 92.6% decrease

**Why Anomaly?**
> Current returns are substantially below the 3-month rolling average (~-81%), and the large rolling deviation triggered the anomaly.

**Root Cause Analysis:**
> Returns fell from 779,170 to 57,442 (-92.63%). Primary causes are the absence of large prior-period returns and concentration of current returns in a single customer, Future Finance Group (two entries totaling 57,442 TL).

### 10. advisory_expense

**Change:** 49.0% increase

**Why Anomaly?**
> Current advisory expense is ~78% higher than its 3-month rolling average, so the rolling-average deviation triggered the anomaly.

**Root Cause Analysis:**
> Advisory expense increased from 216,306.06 to 322,221.34 (+48.97%). The increase is primarily driven by a large payment to BEAN HR YONETIM LTD.STI. of 72,700.0 (45.1%) and additional payments to GORKEM CETIN (44,465.22) and TOKEN FINANSAL TEKNOLOJILER (38,945.45).

### 11. food_expenses

**Change:** 524.1% increase

**Why Anomaly?**
> Both YoY and 3-month rolling deviations are large and beyond thresholds, so YoY and rolling signals together flagged the anomaly.

**Root Cause Analysis:**
> Food expenses rose from 3,345.46 to 20,877.48 (+524.05%). Primary drivers are multiple large supplier payments on the same date, with duplicate entries (e.g., ZORLU YATIRIM A.S., OLUSUM REST.LTD.STI.) and concentrated vendor contributions.

---

## Recommended Actions

- Perform sample-level reconciliations for large receipts and returns to confirm whether movements are one-off receipts or duplicate/erroneous bookings.
- Investigate suspected duplicate postings by cross-checking accounting entries with bank statements and source documents; correct any double postings found.
- Obtain approval and contract evidence for large one-off payments (rent, advisory, hospitality) and enforce stricter authorization for out-of-budget disbursements.
- Review revenue recognition and accrual practices for timing-sensitive interest income and standardize recognition policies to avoid period-to-period timing artefacts.
- Integrate monthly analytical controls (YoY, 3-month rolling, z-score) into operational reporting with automated alerts to finance for rapid triage.
- Create a customer concentration dashboard for key clients and evaluate measures to diversify revenue to reduce single-customer volatility risk.

---

*This report was generated automatically.*