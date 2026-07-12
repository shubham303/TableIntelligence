# 04 — Where data science helps (the payoff mapping)

This is the file the whole study exists for: **each marketing problem → the exact algorithm
that answers it → the deliverable**. Read it with `../data science/` open. When a prospect
describes a pain, you should be able to name the method and the output on the spot.

## The master mapping table

| Marketing question (how a client phrases it) | Data-science method (folder note) | Deliverable |
|---|---|---|
| "Is my client data even clean / what's in it?" | Profiling + outliers (01) | Data-quality pass; honest AOV; whale list |
| "Who are my best/worst customers?" | RFM segmentation (04) | Named segments + value per segment + action lists |
| "Do customers come back?" | Retention cohorts (04) | Cohort retention curves; repeat-rate story |
| "What gets bought together?" | Market basket (06) | Cross-sell/bundle rules ranked by lift |
| "Why did conversion / churn / AOV change?" | Key-driver `explain_metric` (09) | Ranked drivers + plain-English segment rules |
| "Did it *really* change vs last month?" | Period comparison (03) | % change + significance + effect size |
| "What's next quarter?" | Forecast (07) | Point forecast + confidence range |
| "When exactly did it break?" | Changepoint detection (07) | Dated structural breaks to line up with events |
| "Is X related to Y?" | Association testing (02) | Correct test auto-chosen + strength + significance |
| "Which customers will churn / which leads convert?" | Classification (08) | Scored list + why (feature importance / SHAP) |
| "What's this customer worth?" (LTV) | Regression (08) | Predicted value to set acquisition budgets |
| "What natural segments exist?" | Clustering (05) | Discovered personas + profiles |
| "Did our channel/redesign *cause* the lift?" (attribution) | Causal inference (10) | Estimated causal effect + refutation check |

## The value ladder (this sets your *pitch angle*, not a value ranking)
Difficulty and defensibility rise down this list — but **value does not only live at the
bottom.** Each tier delivers real value in a different *shape* (see `../data science/00`):
descriptive sells on *toil removed*, predictive on *foresight*, causal on *"only you can do
this."* Don't read "descriptive" as "cheap."
1. **Descriptive** (01, 03, 04) — "here's what's happening," honestly, from messy data,
   every month, without their team touching a spreadsheet. Low analytical depth but **high
   labour displaced and needed by 100% of clients** — your **report-tier** bread and butter,
   the fastest sample to hand a prospect, and the gateway that makes tiers 3–4 runnable.
2. **Diagnostic** (09, 02, 06) — "here's *why*, and what's related." The interpretation layer
   the whole industry lacks. The core of a good monthly report.
3. **Predictive** (07, 08, 05) — "here's what's coming / who to target." Needs volume →
   **retainer-tier / e-commerce** clients.
4. **Causal** (10) — "here's what actually *drives* it." The senior, hardest-to-refute
   answer; the thing an agency literally cannot produce by hand. Your top differentiator.

## Two motions, mapped to prospect type (from the outreach work)
- **Agencies that already report well** (they have GA4/Looker) — sell the layer *above*
  reporting: diagnostic (09), predictive (07/08), causal (10). Lead with depth, never "you
  don't measure."
- **Agencies/clients that under-report** — start at descriptive/diagnostic (01, 03, 04, 09):
  RFM + cohorts + a "why it changed" decomposition is a complete, cheap, fast sample.

## Scope to data volume (the discipline that keeps you credible)
- **Small (hundreds of orders, report-tier):** stay in 01, 03, 04, 09, 02. RFM, repeat-rate,
  AOV, "what changed & why." Don't promise forecasting/ML/causal — not enough data to trust.
- **Large (e-commerce, retainer-tier):** the full ladder — clustering, basket, forecasting,
  churn/LTV models, causal attribution.
Matching the method to the data size is exactly the deterministic-engine discipline: never
state a number (or sell a model) the data can't support. Over-promising heavy modelling on
thin data is the fastest way to a wrong finding — and one wrong finding kills the client.

## How to run a discovery call with this
1. Ask **what metric they care about** and **what they can't currently answer** about it.
2. Map their answer to a row in the table above.
3. Name the deliverable ("I can decompose *why* CVR dropped into the exact segment") — and,
   if you have their public shape, offer a small sample from the descriptive/diagnostic tier.
4. Let the credibility site + the sample do the closing.
