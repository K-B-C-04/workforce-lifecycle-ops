# Operations Brief: Workforce Lifecycle, H2 2026

**To:** IT & People Operations leadership · **Company:** Larkspur & Vane *(fictional)* · **Data:** synthetic, as of Nov 20, 2026

## Bottom line

Hiring nearly doubled in the fall, and the processes behind it did not scale with it. Four changes would cut setup delays for new hires, recover about **$46K** in outstanding hardware, and lower our exposure to a handful of staffing vendors.

## What the data shows

| Area | Finding | Why it matters |
|---|---|---|
| **Onboarding capacity** | Average cohort size rose from **14 to 28** hires (Sep–Nov vs Jun–Aug), with the same four analysts. One analyst handles **41%** of hires and **52%** of open setup items. | Work concentrates on one person: a single absence stalls a cohort, and new hires start without equipment or access. |
| **Hardware lead time** | Remote hires wait a median of **9 days** for hardware, versus **4 days** at HQ. Remote hires are **34%** of intake. | A third of new hires risk a lost first week. |
| **Offboarding recovery** | Digital steps close quickly (only **2%** of accounts still active), but physical recovery lags: **32 laptops (~$46K)** are not yet returned. **75%** of that value sits with remote leavers, who leave without returning equipment **21%** of the time, versus **5%** at HQ. | Unrecovered devices are both a cost and a security exposure. Laptop wipes wait on returns, and 25 are paused for legal hold. |
| **Vendor concentration** | **3 of 15** vendors supply **52%** of active contractors; the largest alone supplies **23%**. | One vendor's pricing change or delivery failure would affect a quarter of contractor capacity. |
| **Contractor dependence** | Active contractors are up **~40%** in two years. **Client Success** holds **41%** of them. Median engagement: **5.6 months**. | Client-facing capacity relies on short-tenure, outsourced staff. That is a knowledge-retention and service-continuity risk. |

## Recommendations

1. **Rebalance onboarding assignments.** Assign by round-robin per cohort, set a cap on open items per analyst, and review the queue weekly during hiring waves. *Owner: IT Ops lead. Measure: no analyst above 35% of open items.*
2. **Ship remote hardware from the offer-accepted date.** Don't wait for the cohort list. *Owner: IT Ops + Talent. Measure: remote median lead time at or below HQ's.*
3. **Prepaid return kits on day one of notice for remote leavers**, with escalation through the manager at 14 days and HR at 30. *Owner: IT Ops + People. Measure: remote unreturned rate under 8%, outstanding value under $15K.*
4. **Set a vendor share ceiling (e.g. 20%) and qualify a second source for Client Success.** Review vendor mix quarterly. *Owner: Procurement + Client Success. Measure: top-3 share under 45% within two quarters.*

## How these numbers are produced

Every figure comes from [`analysis/analyze.py`](analysis/analyze.py) running on the synthetic datasets in [`data/`](data/). The [live demo](https://k-b-c-04.github.io/workforce-lifecycle-ops/) shows the same views with filters.
