# 04 — Where data science helps (e-commerce payoff mapping)

Read with `../data science/` open. Prospect describes a pain → you name the method and the
deliverable on the spot.

## The master mapping

| Store owner's question | Method (data-science note) | Deliverable |
|---|---|---|
| "What's actually in my data / what's my real AOV?" | Profiling + outliers (01) | Clean totals, honest median AOV, whale list |
| "Who are my best & worst customers?" | RFM (04) | Named segments + value + action lists |
| "Do customers come back? Is it getting better?" | Retention cohorts (04) | Cohort curves; repeat-rate trend |
| "What should I bundle / cross-sell?" | Market basket (06) | Product rules ranked by lift |
| "Why did conversion / revenue drop?" | Key-driver `explain_metric` (09) | Ranked drivers + segment rules |
| "Did it really change, or is it noise/season?" | Period comparison (03) + decompose (07) | % change + significance; deseasonalised trend |
| "What's next quarter's revenue/demand?" | Forecast (07) | Point forecast + confidence range |
| "When did sales structurally break?" | Changepoint (07) | Dated breaks to line up with events |
| "Which customers will churn?" | Classification (08) | Scored at-risk list + why (09) |
| "What's a customer worth?" (set ad budgets) | Regression / LTV (08) | Predicted LTV by segment |
| "What hidden customer types exist?" | Clustering (05) | Discovered personas + profiles |
| "Did the redesign/campaign cause the lift?" | Causal (10) | Estimated effect + refutation |

## The five findings that sell almost every DTC store
Lead with these — high impact, low data requirement, fast to produce:
1. **Repeat-rate is X%, and it's [rising/falling]** — most owners don't know it.
2. **These N At-Risk customers hold $Y of past revenue** — a ready win-back list (RFM).
3. **Your "typical" order is $Z (median), not the $W you quote (mean)** — reframes strategy.
4. **Revenue is down/up, but after removing seasonality the real trend is …** — competence.
5. **Products A+B sell together (lift 3.x) but you don't bundle them** — instant money.

## Scope to volume (keep it honest)
- **Hundreds of orders:** stages 1–2 only — RFM, repeat-rate, AOV, "what changed & why."
- **Thousands+ with months of history:** the full ladder — cohorts, basket, forecasting,
  churn/LTV, causal. Promising heavy modelling on thin data → an untrustworthy number →
  a lost client.

## The connective tissue
E-commerce sits downstream of marketing: acquisition happens on the channels in
`../digital marketing/`, the sale and repeat happen here. The most valuable engagements
**join the two** — "which acquisition channel brings customers with the best LTV and
repeat-rate?" — which is a channel-quality question only you can answer by stitching ad data
to the order table. That join is a service, not a dashboard.
