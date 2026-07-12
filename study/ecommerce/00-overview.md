# E-commerce for a data scientist — the map

E-commerce is your **largest and easiest** market: they have transaction data by default,
owner-operators read their own inbox, and the analyses map cleanly onto your engine. These
notes teach the business well enough that you can read a client's Shopify export and know
what's worth computing.

## Read in this order
| # | File | What you'll get |
|---|------|-----------------|
| 01 | business-model-and-metrics | How an online store makes (and loses) money; the metrics that run it. |
| 02 | the-data-you-receive | Orders, customers, catalog, sessions — the real table shapes and their messiness. |
| 03 | the-analysis-lifecycle | The natural order of analyses across a store's life, from first report to retainer. |
| 04 | where-data-science-helps | Each e-commerce problem → the exact algorithm → the deliverable. |

## The three things to hold onto
1. **An e-commerce business is an acquisition + retention machine.** Money = (customers
   acquired) × (their lifetime value) − (cost to acquire + fulfil). Almost every analysis
   pushes on one of those levers. If a finding doesn't touch acquisition cost, order value,
   or repeat rate, ask why you're computing it.
2. **The order-lines table is the crown jewel.** One row per item per order (customer, date,
   product, quantity, price) unlocks RFM, cohorts, market basket, LTV, and "what changed" —
   most of your highest-value work runs off this one table. (You downloaded **Online Retail
   II** and **Superstore** precisely to practise on it.)
3. **Retention is where the money hides, and where owners are blind.** Most store owners
   obsess over acquisition (traffic, ads) and barely measure whether customers come back.
   Repeat-rate, cohorts, and RFM (data-science note 04) are cheap for you and eye-opening
   for them — your easiest credible sample.

## The mental model
> A store **acquires** customers through channels (see `../digital marketing/`), converts
> them on the site, and tries to make them **buy again**. Every metric measures one of
> those stages; every leak is a segment you can find (data-science note 09).
