# SaaS for a data scientist — the map

SaaS (software-as-a-service: subscription software) is a high-budget target vertical with a
data shape **quite different** from e-commerce. The business is built on *recurring*
revenue, so the whole game is retention and expansion, not one-off sales. Learn the
differences and you can serve SaaS founders and the agencies that market to them.

## Read in this order
| # | File | What you'll get |
|---|------|-----------------|
| 01 | metrics-and-model | MRR, churn, NRR, CAC payback — the subscription metric system. |
| 02 | the-data-and-where-ds-helps | The subscription/event data shape + each problem → algorithm. |

## The three things to hold onto
1. **Recurring revenue changes everything.** A SaaS customer pays every month, so a small
   change in **churn** compounds enormously. The core question is never "did they buy?" but
   "will they *keep* paying, and will they pay *more*?" Retention math (cohorts, churn
   prediction) is the centre of gravity, not a nice-to-have.
2. **The data is event/subscription-shaped, not order-shaped.** Instead of orders you get
   subscriptions (start, plan, MRR, cancel date) and product-usage event logs (logins,
   feature use). Churn has an actual event (cancellation), unlike e-commerce's fuzzy
   "stopped buying."
3. **Usage predicts churn.** Unlike a store, a SaaS sees customers *use* the product daily.
   Declining usage is the leading indicator of churn — a rich, predictive signal e-commerce
   simply doesn't have. This is where your classification models (data-science note 08)
   shine.

## The mental model
> A SaaS **acquires** subscribers, **onboards** them to first value, keeps them from
> **churning**, and **expands** them to bigger plans. Every metric measures one of those;
> usage data gives you an early warning system for the churn one.
