# September 2023 Financial Anomaly Summary Report

---

## Executive Overview

September 2023 shows modest revenue growth alongside notable volatility in several expense and returns categories. While net sales increased slightly, multiple expense lines and returns exhibit significant deviations from both year-over-year and short-term trends, requiring focused attention on liquidity and control processes.

## Detected Anomalies

### 1. hospitality

**Change:** 7.9% increase

**Why Anomaly?**
> This metric was flagged because the current value surged enormously versus both the prior year (YoY +13,530.7% extreme) and the 3-month rolling average (~+106.5%), both far beyond thresholds.

**Root Cause Analysis:**
> Hospitality expenses increased from 225,215.43 to 243,106.77 in September 2023. The rise is primarily driven by a payroll charge of 123,556.06 (50.8% share) and a 91,376.36 payment to SET KURUMSAL HIZMETLER TIC.A.S. (37.6% share); large transactions such as 108,489.97 and 73,850.0 support the increase.

### 2. interest_income

**Change:** -1.1% decrease

**Why Anomaly?**
> Flagged because the YoY change (~+2,482%) and the current value being ~141% above the 3-month rolling average both exceed thresholds, indicating an abnormal pattern in reported interest.

**Root Cause Analysis:**
> Interest income decreased slightly from 16,812.72 TRY to 16,633.5 TRY in September 2023. The change is mainly due to concentration in large 36% coupon bond sales (7,404.13; 4,598.35; 2,564.39 TRY) and timing/compositional effects with fewer smaller entries.

### 3. car_expenses

**Change:** 73.1% increase

**Why Anomaly?**
> This metric spiked with a large YoY increase (~+510%) and a ~55% deviation from the 3-month rolling average; both triggers mark it as an anomaly (yoy_and_rolling).

**Root Cause Analysis:**
> Car expenses rose from 12,224.95 to 21,167.02. The primary driver is a single large payment to OTOKOC OTOMOTIV TIC.A.S. (~10,879.91, including a 10,000.0 transaction on 2023-09-01) and secondary fuel/payments to EDENRED and FULLJET totaling ~6,057.02.

### 4. net_sales

**Change:** 3.3% increase

**Why Anomaly?**
> Net sales were flagged because they jumped ~+236.8% vs last year (YoY), exceeding the YoY threshold; other trend indicators are within normal ranges.

**Root Cause Analysis:**
> Net sales rose to 2,198,287.44 TL from 2,127,701.69. The primary drivers were Future Finance Group contributing 825,130.81 TL (37.5%), plus significant receipts from Bright Future Finance (402,690.69 TL), True North Finance (400,000 TL) and Asset Alliance (316,521 TL).

### 5. local_sales

**Change:** -15.2% decrease

**Why Anomaly?**
> Flagged due to an extreme YoY change (~+189.1% vs threshold) indicating an unusual year-over-year surge pattern that triggered the YoY detection.

**Root Cause Analysis:**
> Local sales declined from 2,045,056.59 to 1,733,498.5. The main drivers are concentration and timing/amount shifts among top contributors—Future Finance Group (825,130.81), Bright Future Finance (402,690.69) and True North Finance (400,000).

### 6. office_rent

**Change:** 21.3% increase

**Why Anomaly?**
> Office rent was flagged because YoY change (~+166.9%) far exceeds the ±30% threshold, driving the anomaly; rolling and z-score are within limits.

**Root Cause Analysis:**
> Office rent increased from 19,050.00 to 23,116.55. The increase is mainly driven by a single large payment of 19,000.00 to AC YAPI INS. SAN.VE TIC.A.S. (82.2% share) and additional Teknopark Istanbul charges (~4,116.55).

### 7. global_sales

**Change:** 79.4% increase

**Why Anomaly?**
> Flagged because of a large YoY spike (+140.1%) combined with a substantial negative deviation from the 3-month rolling average (~-54.9%), triggering the yoy_and_rolling signal.

**Root Cause Analysis:**
> Global sales increased from 82,645.1 to 148,267.94. The primary drivers were two transactions dated 2023-09-22: Pixel Perfect Software for 108,008.0 TL (72.8%) and Clearview Finance for 40,259.94 TL (27.2%).

### 8. software_expense

**Change:** -94.8% decrease

**Why Anomaly?**
> Flagged by the rolling average check: the current amount is ~-99.4% below the 3-month rolling average, indicating prior large charges are absent this period.

**Root Cause Analysis:**
> Software expense fell from 40,073.55 to 2,066.65 due to the removal or absence of prior large charges. The current amount is entirely attributable to OPENAL, LLC (two small transactions: 1,599.61 and 467.04).

### 9. returns

**Change:** -92.6% decrease

**Why Anomaly?**
> Flagged because the current value is ~-81% below its 3-month rolling average; the rolling avg deviation triggered the anomaly.

**Root Cause Analysis:**
> Returns fell from 389,585.0 to 28,721.0. The primary cause is that the month's returns consist solely of a single contributor—Future Finance Group (28,721.0)—suggesting prior-period one-off refunds or timing effects and client concentration.

### 10. advisory_expense

**Change:** 49.0% increase

**Why Anomaly?**
> This metric is flagged because current advisory expense is ~77.6% above the 3-month rolling average, exceeding rolling thresholds while YoY impact is negligible.

**Root Cause Analysis:**
> Advisory expense increased from 108,153.03 to 161,110.67. The increase is primarily driven by payments to BEAN HR YONETIM LTD.STI. (72,700.0, 45.1%), GORKEM CETIN (44,465.22, 27.6%) and TOKEN FINANSAL TEKNOLOJILER A.S. (38,945.45, 24.2%).

### 11. food_expenses

**Change:** 524.1% increase

**Why Anomaly?**
> Flagged as yoy_and_rolling because both YoY and 3-month rolling average deviations are far beyond thresholds, indicating a sharp spike versus historical and recent trends.

**Root Cause Analysis:**
> Food expenses rose from 1,672.73 to 10,438.74. The primary drivers are several concentrated vendor and individual payments made in early September (e.g., ZORLU YATIRIM A.S. 1,020.22; OLUSUM REST.LTD.STI. 718.18; YENIDEN DOGUS LTD.STI. 600.91), indicating a spike from several same-date sizable transactions.

---

## Recommended Actions

- Strengthen pre-payment approval for large one-off payments (set payment thresholds and require secondary approvals).
- Perform monthly cash-flow and timing analysis of collections/returns to identify timing effects from major customers.
- Tighten contract and invoice tracking for rent, advisory and hospitality; verify contract terms when unexpected increases occur.
- Implement budget controls and deviation alerts for variable expense categories (software, advisory) based on 3-month rolling averages.
- Establish transaction-level reporting for securities and interest sources to monitor composition effects on interest income.
- Create a returns-monitoring process with customer-level profiling and follow-up for clients with historically high returns.

---

*This report was generated automatically.*