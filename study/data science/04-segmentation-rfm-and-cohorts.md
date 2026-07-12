# 04 — Segmentation (RFM) & retention cohorts

Code: `analytics/cohort.py` — `rfm`, `retention_cohorts`. Library: plain pandas
(groupby + qcut + pivot). No ML — these are rule-based aggregations, and that's the point:
they're transparent, fast, and work on small data. These are *the* e-commerce insight
primitives and the easiest high-value thing you can sell.

## Part A — RFM segmentation (`rfm`)
### Intuition
Not all customers are equal. RFM scores each customer on three axes that predict future
value better than almost anything else:
- **Recency** — how long since their last purchase (smaller = better).
- **Frequency** — how many times they bought.
- **Monetary** — how much they spent in total.

### How it works
For each customer it computes R, F, M, then assigns a **quintile score 1–5** on each
(via `qcut` — rank into 5 equal buckets). Recency is reversed (a recent buyer gets a 5).
F and M are averaged into an "FM" score. Then (R, FM) maps to canonical named segments:
- **Champions** (R≥4, FM≥4) — recent, frequent, high-spend. Your best customers.
- **Loyal** (R≥3, FM≥3).
- **Potential Loyalist** (R≥4, FM≥1) — recent, not yet high-value.
- **At Risk** (R≤2, FM≥3) — used to be great, going quiet. **The money segment for
  win-back campaigns.**
- **Hibernating** (R≤2, FM≤2) — lapsed and low-value.
- **Others** — everyone else.

Output: customers-per-segment, and total monetary value per segment (so you can say "At
Risk holds $X of historical revenue that's slipping away").

### Pitfalls
- Needs enough distinct customers for 5 quintiles; on tiny data the code falls back to
  coarser bins.
- The segment thresholds are the industry-standard scheme, not gospel — fine for a first
  read, tune per client.
- Quintiles are *relative*: everyone's ranked against this client's own base, so a
  "Champion" for a small brand ≠ a Champion for a big one. That's usually what you want.

## Part B — Retention cohorts (`retention_cohorts`)
### Intuition
"Do customers come back?" Group customers by the **month of their first purchase** (their
cohort), then track what fraction are still active 1, 2, 3… months later. This is the
single clearest picture of whether a business is building a customer base or leaking one.

### How it works
Each customer's cohort = their first-purchase month. `months_since` = calendar months
between each later purchase and that first month. A pivot gives a **cohort × months-since**
matrix of retained-customer counts, and dividing by each cohort's initial size gives
**retention rates** (fractions). Month 0 is always 1.0 (100% by definition).

### Reading it
- Read **down a column** (e.g. month-3 retention) to see whether newer cohorts retain
  better or worse than older ones — i.e. is the product/marketing improving?
- Read **across a row** to see a single cohort's decay curve.
- A healthy business flattens to a stable repeat-rate; a leaky one decays to near zero.

### Pitfalls
- Recent cohorts have fewer months of history — don't compare a 1-month-old cohort's
  "month 6" (it has none) to an old one's.
- Needs a customer id that's stable across orders. (In Olist: use `customer_unique_id`,
  not the per-order `customer_id`.)

## Marketing / e-commerce angle
- **RFM is the fastest paid deliverable you can offer**, and it works on small report-tier
  clients (hundreds of orders) where forecasting/ML would be untrustworthy. "Here are your
  38 At-Risk customers holding $12k of past revenue — here's the win-back list."
- **Retention cohorts reframe an agency from 'we get clicks' to 'we get repeat customers'**
  — the retention story that defends a retainer.
- Both feed campaign targeting directly: Champions → loyalty/referral; At Risk → win-back;
  Potential Loyalist → nurture. This is where analysis turns into a marketing action, which
  is what the client is actually paying for.
