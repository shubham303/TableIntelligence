# 02 — SaaS data shape & where data science helps

## The data you'll receive
1. **Subscriptions table** — `customer_id, plan, mrr, start_date, cancel_date, status`.
   The backbone: MRR, churn, NRR, cohorts all come from here.
2. **Customers / accounts** — `customer_id, signup_date, acquisition_channel, industry,
   company_size, seats`.
3. **Usage / product events** — `customer_id, timestamp, event/feature`. Often the biggest
   table; the churn early-warning signal lives here (aggregate to per-customer usage
   trends).
4. **Billing** (Stripe/Chargebee exports) — invoices, payments, failed charges (involuntary
   churn from card failures is a real, fixable leak).
5. **Marketing/CRM** (HubSpot) — the funnel from lead → trial → paid.

Messiness to expect: **involuntary vs voluntary churn** conflated; trial users mixed with
paid; plan changes recorded as cancel+new (breaking naive churn counts); usage events in
inconsistent schemas. Data-science note 01 is still your first pass.

## The payoff mapping

| SaaS question | Method (data-science note) | Deliverable |
|---|---|---|
| "Break down my MRR movement." | Key-driver decomposition (09) + aggregation | New/expansion/contraction/churn waterfall |
| "Which customers will churn?" | Classification (08) on usage+account features | Scored at-risk accounts + why (SHAP, note 09) |
| "Why do customers churn?" | Key-driver `explain_metric` (09) | Ranked churn drivers + segment rules |
| "When did this account start slipping?" | Changepoint on usage (07) | Dated usage drop → proactive outreach trigger |
| "Do cohorts retain better over time?" | Retention cohorts (04, by subscription month) | NRR/retention cohort curves |
| "Who will upgrade (expansion)?" | Classification (08) | Upsell-target list |
| "What's next quarter's MRR?" | Forecast (07) | MRR forecast + confidence range |
| "What account types exist?" | Clustering (05) | Behavioural account segments |
| "Does onboarding/feature-X *cause* retention?" | Causal (10) | Estimated effect + refutation |

## The signature SaaS deliverable: a churn early-warning system
This is the flagship because it's high-value and uniquely fits SaaS data:
1. Aggregate usage events into per-customer trend features (logins/week, feature breadth,
   usage changepoints — note 07).
2. Train a churn **classifier** (note 08) on customers with known outcomes.
3. Score active customers → ranked at-risk list, each with a **SHAP explanation** (note 09)
   of *why* — so the client's success team knows what to fix.
4. Feed it monthly. That cadence is the retainer.
A store can't build this (no daily usage signal); a SaaS founder often lacks the data-science
team to. That's your wedge.

## Scope to volume
Churn/expansion models need a decent number of customers *and* churn events to be trustworthy
— comfortable for a Series-A+ SaaS, shaky for a 50-customer startup. For tiny SaaS, stay
descriptive: MRR waterfall, cohort retention, activation rate. Don't ship a churn model that
trained on 12 cancellations.
