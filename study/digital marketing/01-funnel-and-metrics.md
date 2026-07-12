# 01 — The funnel & the metrics that run the money

If you learn one marketing concept, learn the funnel and the dozen metrics hanging off it.
Every client conversation, dashboard, and report is organised around these.

## The funnel
Marketers picture the customer journey as a funnel — many enter the top, few reach the
bottom. A common framing (AARRR / "pirate metrics"):

1. **Awareness** — people discover the brand (impressions, reach).
2. **Acquisition** — they visit / click (sessions, clicks, traffic).
3. **Activation** — first meaningful action (signup, add-to-cart, first visit quality).
4. **Revenue / Conversion** — they buy (orders, conversions, revenue).
5. **Retention** — they come back (repeat purchase, churn).
6. **Referral** — they bring others (reviews, shares, referrals).

Each stage has a **conversion rate** to the next, and money leaks at every step. "Where is
the funnel leaking?" is the perennial question — and a decomposition question (data-science
note 09).

## The metrics (know these cold)
**Volume / top-of-funnel**
- **Impressions** — times an ad/listing was shown.
- **CTR (click-through rate)** = clicks ÷ impressions. Are people interested?
- **Sessions / Traffic** — visits to the site.

**Cost**
- **CPC (cost per click)** = spend ÷ clicks.
- **CPM (cost per mille)** = cost per 1,000 impressions.
- **CPL / CPA (cost per lead / acquisition)** = spend ÷ leads (or customers).
- **CAC (customer acquisition cost)** = total spend to win one customer. The number that
  decides whether a channel is viable.

**Value / bottom-of-funnel**
- **Conversion rate (CVR)** = conversions ÷ sessions (or clicks). The master efficiency
  metric.
- **AOV (average order value)** = revenue ÷ orders. (Report the *median* when skewed —
  data-science note 01.)
- **LTV / CLV (customer lifetime value)** — total profit from a customer over their life.
  Predictable with regression (note 08).
- **Repeat purchase rate / Churn rate** — do they come back, or leave? (Cohorts, note 04.)

**The two ratios that decide everything**
- **ROAS (return on ad spend)** = revenue ÷ ad spend. Channel-level "did this pay?"
- **LTV : CAC** — lifetime value vs cost to acquire. The health metric of the whole
  business. Rule of thumb: 3:1 is healthy; below 1:1 you lose money on every customer.

## Why this matters for you
- **Every metric is a column or a computed ratio** in the data a client hands you. Knowing
  the vocabulary means you can read their export without a translator.
- **The interesting questions are all data-science questions in disguise:**
  - "Why did CVR drop?" → key-driver decomposition (note 09).
  - "Which customers will churn?" → classification (note 08).
  - "What's next quarter's revenue?" → forecast (note 07).
  - "Did the change *cause* the ROAS lift?" → causal (note 10).
  - "Who are our best customers?" → RFM (note 04).
- **The funnel is a decomposition tree.** When a bottom metric moves, the cause is a
  specific upstream stage × segment — which is exactly what `explain_metric` finds.

## The trap to avoid
Marketers optimise **vanity metrics** (impressions, CTR) that feel good but don't move
money. Your value is tying everything back to **revenue, CAC, LTV, and ROAS** — the metrics
a business owner actually cares about. Always ask "does this connect to money?" — it's the
same discipline as "does this connect to effect size, not just significance."
