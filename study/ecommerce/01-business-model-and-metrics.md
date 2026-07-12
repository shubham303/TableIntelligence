# 01 — How an online store makes money, and the metrics that run it

## The unit economics (the whole business in one line)
> **Profit per customer = LTV − CAC − COGS/fulfilment.**
- **CAC** (customer acquisition cost) — ad spend + agency fees ÷ new customers.
- **LTV** (lifetime value) — total gross profit a customer delivers before they churn.
- **COGS / fulfilment** — cost of goods, shipping, payment fees, returns.
A store lives or dies on **LTV : CAC** (healthy ≈ 3:1). Everything below is a lever on it.

## The metrics, grouped by lever
**Acquisition**
- Sessions / traffic, by channel.
- **Conversion rate (CVR)** = orders ÷ sessions. The master efficiency number; small % moves
  = large revenue.
- **CAC** and **ROAS** (revenue ÷ ad spend) — is acquisition paying?

**Order economics**
- **AOV** (average order value) = revenue ÷ orders. Report the **median** when skewed
  (data-science note 01).
- **Units per transaction**, **basket composition** — what's in an order (note 06).
- **Gross margin** — the part of revenue you actually keep.

**Retention (the blind spot)**
- **Repeat purchase rate** — % of customers who buy again. The single most under-measured,
  high-impact number.
- **Purchase frequency** and **time-between-orders**.
- **Churn** — customers who stop buying (fuzzy in e-comm: no cancellation event, so defined
  as "no purchase in N months").
- **LTV** — the payoff of retention; predictable via regression (note 08).

**Catalog / product**
- Best/worst sellers, **product affinity** (bought-together, note 06), return rate by SKU,
  price elasticity.

## The seasonality fact
E-commerce is **heavily seasonal** (Q4/holidays, sales events, category cycles). This is why
you never read a raw month-over-month number without decomposing trend from seasonality
(data-science note 07) — mistaking a December spike for growth is the classic amateur error,
and separating them is a mark of competence a client notices.

## The traps to spot in a client's numbers
- **Vanity on acquisition, silence on retention.** Owners quote traffic and AOV, rarely
  repeat-rate. That gap is your opening.
- **Mean AOV on skewed orders** overstates the "typical" order — a few whales pull it up.
- **Revenue without margin.** A discount-driven revenue spike can be unprofitable. Always
  ask whether a number is revenue or profit.
- **Gross of returns.** Returns silently erase revenue and margin; a store that ignores them
  overstates performance.

## Why this matters for you
Each metric is a column or ratio in the order/customer tables. Knowing the levers means a
client's export instantly suggests the analysis: flat repeat-rate → cohorts + RFM;
soft CVR → key-driver decomposition; seasonal confusion → decomposition; "which products" →
basket. You read the data through the business, not the other way round.
