# 01 — SaaS metrics & the subscription model

## The recurring-revenue core
- **MRR / ARR** (monthly / annual recurring revenue) — the heartbeat number. The sum of all
  active subscriptions' monthly value. ARR = MRR × 12.
- **MRR movements** — MRR is decomposed into: **new** (new customers) + **expansion**
  (upgrades) − **contraction** (downgrades) − **churned** (cancellations). This waterfall is
  *the* SaaS report, and it's a decomposition (data-science note 09).

## Churn — the number that compounds
- **Customer churn rate** — % of customers who cancel in a period.
- **Revenue churn** — % of MRR lost. Differs from customer churn when big and small accounts
  churn at different rates (losing one whale ≠ losing one small account).
- **Net Revenue Retention (NRR)** — MRR from existing customers this period vs last,
  *including* expansion. **NRR > 100%** means the existing base grows even with zero new
  sales — the single most prized SaaS metric. Investors live by it.
- **Gross retention** — same but without expansion (pure leakage).

## Acquisition economics
- **CAC** — cost to acquire a subscriber.
- **CAC payback period** — months of subscription revenue to recover CAC. < 12 months is
  healthy.
- **LTV** — here it's driven by churn: `LTV ≈ ARPA / churn rate` (lower churn → dramatically
  higher LTV). **LTV : CAC ≥ 3:1** is the target.
- **ARPA / ARPU** — average revenue per account/user.

## Engagement / leading indicators
- **Activation rate** — % of signups reaching "first value" (the aha moment). Weak
  activation predicts early churn.
- **DAU/MAU (stickiness)** — daily over monthly active users; how habitual the product is.
- **Feature adoption** — which features correlate with retention.
- **Trial → paid conversion** — for freemium/trial models.

## Why the differences from e-commerce matter to you
- **Churn has a real event** (a cancellation date) → clean labels for a churn *classifier*
  (data-science note 08), which e-commerce lacks.
- **Usage is a time series per customer** → declining-usage changepoints (note 07) are a
  churn early-warning.
- **Expansion exists** → "which customers are likely to upgrade?" is a second classification
  problem (upsell targeting) with real money behind it.
- **Cohorts are about revenue retention over months**, not repeat purchases (note 04, applied
  to subscription months).

## Traps to spot
- **Confusing customer churn with revenue churn** — a business can lose many small accounts
  yet grow MRR (or vice-versa). Always ask which.
- **Vanity signups** — signups without activation are noise; tie everything to activated,
  paying, retained users.
- **Averaging over plan tiers** — enterprise and self-serve behave nothing alike; segment
  first (clustering, note 05).
