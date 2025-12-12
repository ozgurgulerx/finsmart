# September 2023 Financial Anomaly Summary Report

---

## Executive Overview

September 2023 shows concentrated volatility across several revenue and expense lines driven by large single transactions, timing effects and customer/supplier concentration. Net sales edged up slightly while returns, software expenses and some cost categories declined sharply; hospitality, advisory, car, rent, global sales and food expenses showed notable increases. Overall, seasonality and concentration/timing issues materially affected month-over-month and year-over-year comparisons.

## Detected Anomalies

### 1. hospitality

**Change:** 7.9% increase

**Why Anomaly?**
> Flagged because current value jumped massively versus same month last year (YoY +13,530.7%) and deviated strongly from the 3-month rolling average (106.5%), triggering the yoy_and_rolling signal.

**Root Cause Analysis:**
> Hospitality rose from 225,215.43 to 243,106.77 in September 2023. The increase is primarily driven by a payroll charge of 123,556.06 (50.8%) labeled "2023/EYLUL UCRET BORDROSU" and a 91,376.36 payment to SET KURUMSAL HIZMETLER TIC.A.S. (37.6%), supported by large transactions such as 108,489.97 and 73,850.0.

### 2. interest_income

**Change:** 1.1% decrease

**Why Anomaly?**
> Flagged due to an extraordinary YoY swing (+2,482%) combined with large deviation from the 3-month rolling average (140.8%), resulting in a yoy_and_rolling signal despite a modest month-over-month change.

**Root Cause Analysis:**
> Interest income decreased from 16,812.72 to 16,633.50 TRY. The decline is driven by concentration in large 36% coupon bond sales (7,404.13; 4,598.35; 2,564.39 TRY) and timing/compositional effects; a shift toward large transactions and fewer smaller entries produced a slight overall decline.

### 3. car_expenses

**Change:** 73.1% increase

**Why Anomaly?**
> Flagged because YoY change was extremely large (+510.1%) and the current value far exceeded the 3-month rolling average (+55.2%), triggering the yoy_and_rolling signal.

**Root Cause Analysis:**
> Car expenses rose from 12,224.95 to 21,167.02. The primary driver is a single large payment to OTOKOC OTOMOTIV TIC.A.S. of 10,879.91 (including a 10,000.0 transaction on 2023-09-01), with secondary contributions from EDENRED KURUMSAL COZUMLER A.S. and FULLJET AKARYAKIT LTD.STI. (~3,033.01 and ~3,024.01).

### 4. net_sales

**Change:** 3.3% increase

**Why Anomaly?**
> Detected mainly due to a massive YoY increase (+236.8%) compared with the same month last year; other signals (rolling deviation, z-score) were within thresholds.

**Root Cause Analysis:**
> Net sales rose from 2,127,701.69 to 2,198,287.44. The primary drivers were large receipts: Future Finance Group 825,130.81 (37.5%), Bright Future Finance 402,690.69, True North Finance 400,000.0 and Asset Alliance 316,521.0.

### 5. local_sales

**Change:** 15.2% decrease

**Why Anomaly?**
> Flagged because YoY change was large (YoY +189.1% relative to prior year), so the YoY signal triggered the anomaly despite rolling and z-score being within acceptable ranges.

**Root Cause Analysis:**
> Local sales declined from 2,045,056.59 to 1,733,498.5. The main drivers are concentration and timing/amount changes among top contributors: Future Finance Group 825,130.81 (47.6%), Bright Future Finance 402,690.69 (23.2%) and True North Finance 400,000.0 (23.1%).

### 6. office_rent

**Change:** 21.3% increase

**Why Anomaly?**
> Flagged mainly because YoY change was large (+166.9%) compared to last year; rolling deviation and z-score were within thresholds but YoY surge triggered detection.

**Root Cause Analysis:**
> Office rent increased from 19,050.00 to 23,116.55. The increase is driven by a single large payment of 19,000.00 to AC YAPI INS. SAN.VE TIC.A.S. (82.2% share), with additional Teknopark Istanbul charges (~4,116.55) contributing.

### 7. global_sales

**Change:** 79.4% increase

**Why Anomaly?**
> Flagged because the month shows a huge YoY surge (+140.1%) while simultaneously deviating substantially from the 3-month rolling average (-54.9%), leading to a yoy_and_rolling detection.

**Root Cause Analysis:**
> Global sales increased from 82,645.10 to 148,267.94. The primary drivers were two transactions dated 2023-09-22: Pixel Perfect Software 108,008.0 (72.8%) and Clearview Finance 40,259.94 (27.2%).

### 8. software_expense

**Change:** 94.8% decrease

**Why Anomaly?**
> Flagged because the value dropped dramatically relative to the 3-month rolling average (-99.4%), triggering the rolling signal in absence of meaningful YoY data.

**Root Cause Analysis:**
> Software expense decreased from 40,073.55 to 2,066.65. The reduction is primarily due to the absence of prior large charges. The current amount is entirely attributable to OPENAL, LLC (2,066.65), reflected in two smaller transactions (1,599.61 and 467.04).

### 9. returns

**Change:** 92.6% decrease

**Why Anomaly?**
> Flagged because current returns (~28,721) are ~81% below the 3-month rolling average (~150,950), triggering the rolling average deviation signal.

**Root Cause Analysis:**
> Returns fell from 389,585.0 to 28,721.0. The primary cause is that the month's returns consist solely of a single contributor—Future Finance Group at 28,721.0—indicating prior-period one-off refunds or timing and client concentration effects.

### 10. advisory_expense

**Change:** 49.0% increase

**Why Anomaly?**
> Flagged mainly because current value (~161,110.67) is ~77.6% above the 3-month rolling average, triggering the rolling signal; YoY and z-score were weaker.

**Root Cause Analysis:**
> Advisory expense rose from 108,153.03 to 161,110.67. The increase is primarily driven by payments to BEAN HR YONETIM LTD.STI. 72,700.0 (45.1%), GORKEM CETIN 44,465.22 (27.6%) and TOKEN FINANSAL TEKNOLOJILER ANONIM SIRKETI 38,945.45 (24.2%).

### 11. food_expenses

**Change:** 524.1% increase

**Why Anomaly?**
> Flagged because both YoY (-63.7%) and rolling-average deviation (-58.1%) exceeded thresholds, producing a yoy_and_rolling detection tied to concentrated same-date large payments.

**Root Cause Analysis:**
> Food expenses rose from 1,672.73 to 10,438.74. The primary drivers are concentrated large vendor and individual payments made in early September—e.g., ZORLU YATIRIM A.S. 1,020.22, OLUSUM REST.LTD.STI. 718.18 and YENIDEN DOGUS LTD.STI. 600.91—indicating a spike from several sizable same-date transactions.

---

## Recommended Actions

- Validate large single payments and receipts by reviewing accounting codes and descriptions to confirm one-off versus recurring nature.
- Implement concentration limits and timing controls for top customers and suppliers (scheduled collections/refunds) to reduce client/partner concentration risk.
- Review revenue recognition and recording policies for bonds and investment instruments; publish a monthly timing disclosure schedule to reduce timing effects.
- Tighten contract and invoice tracking for software and advisory spend; enforce pre-approval thresholds for high-value vendor payments.
- Reassess expense policies and limits for food, hospitality and car expenses; strengthen company card controls and refund procedures.
- Establish monthly anomaly reporting with management alert thresholds and a defined investigation and remediation workflow for high-impact items.

---

*This report was generated automatically.*