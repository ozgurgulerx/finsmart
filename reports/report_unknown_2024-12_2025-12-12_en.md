# December 2024 Financial Anomaly Summary Report

---

## Executive Overview

In December 2024 the company's financials showed notable volatility driven by large one-off receipts and several suspicious high-value expense postings. Domestic and net sales experienced significant increases while several expense categories (software, advisory, rent, food) were impacted by single large transactions or potential duplicate postings. These anomalies may affect monthly profitability and cash flow forecasts and require prompt verification and remediation.

## Detected Anomalies

### 1. software_expense

**Change:** 1231.5% increase

**Why Anomaly?**
> An extreme year-over-year surge (191,208.50 vs 4,133.30; ~4,526% increase) combined with a large deviation from the 3-month rolling average (~57.6% below) triggered the anomaly via the YoY and rolling-average signals.

**Root Cause Analysis:**
> Software expense rose from 7,180.27 TL to 95,604.25 TL in December 2024, a 1,231.49% increase. The surge is primarily driven by a 73,818.18 TL charge to "TOKEN FİNANSAL" (77.2% share) and a 15,781.41 TL charge to "INGAGE DIGITAL" (16.5% share), with smaller entries (5,940.00 TL, 64.66 TL) contributing.

### 2. interest_income

**Change:** 285.8% increase

**Why Anomaly?**
> Both YoY and 3-month rolling comparisons are far outside thresholds (YoY ~3957%, rolling deviation ~365%), with the monthly value spiking from 1,546 to 62,718; the combination of these signals (YoY and rolling) triggered the detection.

**Root Cause Analysis:**
> Interest income rose from 8,129.09 to 31,359.04 in December 2024, a 285.76% increase driven primarily by a single bond sale entry of 29,871.61 that accounts for 95.3% of the change. Supporting small daily interest entries exist, indicating the spike is essentially due to the one-off bond sale rather than recurring operations.

### 3. local_sales

**Change:** 85.9% increase

**Why Anomaly?**
> YoY increase (+354%) and 3-month rolling deviation (+32.8%) both exceed thresholds, and a rising z-score (2.09) further supports that this is a true anomaly (YoY and rolling signals).

**Root Cause Analysis:**
> Domestic sales increased primarily due to large collections from Pathway Investors (52.1% share) and QuantaPay (37.0% share). Sample transactions dated 2024-12-19 show concentrated high-value receipts from these customers driving most of the increase.

### 4. net_sales

**Change:** 8.7% increase

**Why Anomaly?**
> A massive YoY jump (~308.1%) and a Z-score of 2.08 exceed anomaly thresholds, indicating the year-over-year change is the primary signal.

**Root Cause Analysis:**
> Net sales increased by 8.7% in December 2024 versus the prior month. The rise is primarily driven by large customer receipts, with Pathway Investors accounting for 48.1% and QuantaPay 34.2% of the incremental amount.

### 5. office_rent

**Change:** 21.7% increase

**Why Anomaly?**
> Year-over-year change (~282%) is well beyond the ±30% threshold, which triggered the anomaly despite rolling-average deviation and Z-score being within limits.

**Root Cause Analysis:**
> Office rent increased primarily due to two large payments (30,000 TL and 29,662.90 TL) which together account for roughly 82.2% of the uplift. Evidence shows duplicate postings of these payments, indicating booking errors or double billing as the main contributing factors.

### 6. advisory_expense

**Change:** 340.5% increase

**Why Anomaly?**
> Advisory expense spike is anomalous because both YoY change (~93.6%) and the 3-month rolling deviation (~83.8%) exceed thresholds; the alert was triggered by the combined YoY and rolling signals.

**Root Cause Analysis:**
> Advisory expenses rose by 340.5% in December 2024, driven mainly by a single ROBOTİK LAB payment of 146,495.33 TL which accounts for 48.8% of the increase, together with three other large consultant payments (13.7%, 13.2% and 10.8% shares). Duplicate entries in the evidence sample indicate possible recording errors or duplicate billing that should be investigated.

### 7. car_expenses

**Change:** 34.5% decrease

**Why Anomaly?**
> Both YoY and rolling-average comparisons show unusually large declines (YoY -65%, rolling -58%), triggering the anomaly via the combined YoY and rolling signals.

**Root Cause Analysis:**
> Car expenses decreased by 34.5% in December 2024 versus the prior month. The decline is driven primarily by reduced fuel spending at MAYGOLD PETROL (the sole recorded contributor at 100%) and sample entries suggest duplicated transaction records or data-cleanup effects impacted the reported total.

### 8. food_expenses

**Change:** 20.1% increase

**Why Anomaly?**
> Year-over-year change (~56.7%) exceeds the ±30% threshold, so the YoY signal triggered the anomaly even though rolling deviation and Z-score are within limits.

**Root Cause Analysis:**
> Food expenses increased primarily due to a single 'SET KURUMSAL' charge of 174,737.27 TL which accounts for 91.2% of the increase. Duplicate entries in the evidence sample point to a one-off large payment or a possible booking duplication as the main cause.

---

## Recommended Actions

- Verify source documents for high-value software, advisory, food and rent postings; correct any duplicate or erroneous bookings and update accounting records.
- Classify one-off items (e.g. bond sale) separately from recurring operating income to avoid distorting trend analyses and forecasting.
- Confirm large customer collections at the customer-contract level and reconcile cash receipts to invoices and bank statements.
- Strengthen approval controls for large payments (dual approvals, threshold limits, mandatory supporting documentation) and implement automated duplicate-transaction detection.
- Initiate an accounting data-quality cleanup to resolve duplicate invoices, mispostings and currency conversion issues identified in the evidence.
- Assess short-term liquidity impact with management and adjust cash forecasts/working capital plans to reflect anomaly-driven variances.

---

*This report was generated automatically.*