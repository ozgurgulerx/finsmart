# December 2024 Financial Anomaly Summary Report

---

## Executive Overview

December 2024 shows concentrated large positive cash receipts raising net and domestic sales, while several expense categories experienced significant one-off or duplicated postings that materially affected month totals. These patterns suggest a mix of operational seasonality and data/booking issues requiring targeted validation and control enhancements.

## Detected Anomalies

### 1. software_expense

**Change:** 1231.5% increase

**Why Anomaly?**
> Extreme YoY change (≈4526%) and large deviation from the 3-month rolling average triggered the alert; both YoY and rolling-average signals were activated.

**Root Cause Analysis:**
> Software expense rose from 7,180.27 TL to 95,604.25 TL in December 2024, a %1231.4854455333852 increase. The surge is primarily driven by a 73,818.18 TL charge to "TOKEN FİNANSAL" (77.2% share) and a 15,781.41 TL charge to "INGAGE DIGITAL" (16.5% share), with smaller entries (5,940.00 TL, 64.66 TL) contributing.

### 2. interest_income

**Change:** 285.8% increase

**Why Anomaly?**
> Both YoY growth (very large) and rolling-average deviation (~365%) are extreme; the surge is primarily driven by a one-off bond sale entry.

**Root Cause Analysis:**
> Interest income rose from 8,129.09 to 31,359.04 in December 2024, a %285.7632281104035 increase driven primarily by a single bond sale entry of 29,871.61 that accounts for 95.3% of the change. Supporting entries of 1,114.75 and 372.68 exist, indicating the surge is essentially due to the one-off bond sale rather than recurring operations.

### 3. local_sales

**Change:** 85.9% increase

**Why Anomaly?**
> Marked YoY increase (~354%), ~33% above the 3-month rolling average and Z-score 2.09 triggered the anomaly; growth is concentrated in a few large customer receipts.

**Root Cause Analysis:**
> Domestic sales increased by %85.9 in December 2024, primarily driven by large collections from Pathway Investors (52.1% share) and QuantaPay (37.0% share). Sample transactions dated 2024-12-19 indicate concentrated high-value receipts from these customers as the main cause of the anomaly.

### 4. net_sales

**Change:** 8.7% increase

**Why Anomaly?**
> Flagged due to very high YoY jump (≈308%) and Z-score above threshold (2.08); rolling average deviation was within limits but YoY signal is decisive.

**Root Cause Analysis:**
> Net sales increased by 8.7% in December 2024 versus the prior month. The rise is primarily driven by large customer receipts, with Pathway Investors accounting for 48.1% and QuantaPay 34.2% of the incremental amount.

### 5. office_rent

**Change:** 21.7% increase

**Why Anomaly?**
> Significant year-over-year spike (145k vs 38k last year, +282% YoY) caused the flag; rolling-average and z-score remained within bounds but YoY exceeded thresholds.

**Root Cause Analysis:**
> Office rent increased by 21.7% in December 2024, primarily driven by two large payments (30k TL and 29,662.9 TL) which together account for roughly 82.2% of the uplift. Evidence shows duplicate postings of these payments, indicating booking errors or double billing as the main contributing factors.

### 6. advisory_expense

**Change:** 340.5% increase

**Why Anomaly?**
> Both YoY and rolling-average deviations exceeded alert limits (large year-over-year spike plus substantial deviation from 3-month rolling avg), so anomaly flagged.

**Root Cause Analysis:**
> Advisory expenses rose by 340.5% in December 2024, driven mainly by a single ROBOTİK LAB payment of 146,495.33 TRY which accounts for 48.8% of the increase, together with three other large consultant payments (13.7%, 13.2% and 10.8% shares). Duplicate entries in the evidence sample indicate possible recording errors or duplicate billing that should be investigated.

### 7. car_expenses

**Change:** 34.5% decrease

**Why Anomaly?**
> Both YoY (-65.3%) and rolling-average deviation (-58.4%) exceed thresholds, indicating an unusually large drop driven by non-recurring or data-cleanup effects.

**Root Cause Analysis:**
> Car expenses decreased by 34.5% in December 2024 versus the prior month. The decline is driven primarily by reduced fuel spending at MAYGOLD PETROL (the sole recorded contributor at 100%) and the sample entries suggest duplicated transaction records or data-cleanup effects impacting the reported total.

### 8. food_expenses

**Change:** 20.1% increase

**Why Anomaly?**
> Flagged mainly for year-over-year surge (≈56.7% YoY) exceeding ±30% threshold, while rolling-average and z-score stayed within limits.

**Root Cause Analysis:**
> Food expenses increased by 20.1% in December 2024, primarily driven by a single 'SET KURUMSAL' charge of 174737.27 TL which accounts for 91.2% of the increase. Duplicate entries in the evidence sample point to a one-off large payment or a possible booking duplication as the main cause.

---

## Recommended Actions

- Validate invoices and source documents for large software, advisory and food expense items; reverse or recover amounts if improper or duplicated.
- Investigate duplicated rent and advisory postings; correct accounting entries and implement reconciliation procedures to prevent repeats.
- Confirm bond sale accounting and tax treatment for interest income with treasury and tax teams; record any necessary reclassifications.
- Update short-term cash forecasts to reflect concentrated customer collections and assess customer concentration risk; consider adjusting credit/collection terms.
- Implement automated rules to flag high-value single transactions and potential duplicate entries at booking time.
- Enforce dual-approval for high-value payments and tighten vendor onboarding/verification processes.
- Ensure full audit trail storage (invoices, bank proofs, contracts) and run sample-based internal audit checks on anomalous items.
- Prepare disclosures or adjustments for year-end close and tax filing reflecting investigated corrections and their financial statement impact.

---

*This report was generated automatically.*