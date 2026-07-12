# 09 — Model interpretation & key-drivers ("why?")

Code: `analytics/interpretation.py` (`feature_importance`, `explain_prediction`) and
`analytics/insights.py` (`explain_metric`). Libraries: scikit-learn (permutation +
decision tree), **shap**.

A prediction is worth little to a client without the *why*. This family opens the black
box. Two of these explain a trained model; one explains a metric directly with no model to
train first.

## A — Global importance: what drives the model? (`feature_importance`)
**Permutation importance**, computed on the held-out test split: shuffle one feature's
values and measure how much the model's score drops. Big drop = the model relied on that
feature = it's important. Model-agnostic, and measured over the *original* named columns
(before one-hot expansion), so each score maps to a column the client recognises.
- Reading: a ranked list, most-important first.
- Pitfall: importance = "the model used it", **not** "changing it changes the outcome"
  (that's causation, note 10). Correlated features can also share/split importance.

## B — Local explanation: why *this* prediction? (`explain_prediction`)
**SHAP** values for a single row: they fairly attribute the prediction across features,
splitting it into "this customer's `recency` pushed churn-risk +0.12, their `spend` pulled
it −0.05…", summing from a base value to the final prediction. One-hot contributions are
summed back to the original column so the story stays readable.
- Use it to answer "why did the model flag *this specific* customer/lead?" — the
  per-customer justification that makes a client trust the list.
- Pitfall: SHAP explains the *model's* reasoning, which is only as right as the model.

## C — Key-driver without a model: `explain_metric` (the workhorse)
This is the one you'll use most in reports, and it needs no separate trained model. It fits
a **shallow decision tree** (max depth 3) with the metric as the target and every other
column as a feature, then reads two things off the tree:
1. **`drivers`** — ranked feature importances: the columns that most drive the metric.
2. **`rules`** — human-readable segment rules exported as text, e.g.
   *"monetary > 500 AND region = NE → churn rate 0.08"*. This is what actually goes in a
   client finding — a plain-English segment, not a coefficient.
It also returns **`explained`** — the tree's R²/accuracy — i.e. how much of the metric these
simple segments actually account for (a low value = "don't over-trust these rules").
The tree is kept deliberately shallow: the deliverable is *interpretable segments*, not a
black-box predictor (use note 08 for prediction).

### Why `explain_metric` is the money function for agencies
An agency manager can *see* that conversions dropped. They usually **can't decompose it**.
`explain_metric` turns "conversions are down" into "the drop is concentrated in mobile
users from one city on one campaign" — a cause-shaped, actionable segment. That decomposition
is the single biggest thing separating your report from a dashboard.

## Reading the outputs — one caution across all three
Importance and driver rankings describe **association inside the data**, not
interventions. "`discount` is the top driver of `order_value`" does **not** license "cut
discounts to raise order value." To make that leap you need note 10. Say "driver/associated
with", never "causes", unless you've done the causal work.

## Marketing / e-commerce angle
- **`explain_metric` on any KPI** — "what drives conversion rate / churn / AOV / review
  score?" → ranked drivers + segment rules, straight into the monthly report.
- **`feature_importance`** to headline a churn/lead model: "the top three signals of churn
  are X, Y, Z."
- **`explain_prediction`** to justify a specific targeting decision to a skeptical client:
  "we flagged this account because…". Explanation is what converts a model output into
  something a client will act on.
