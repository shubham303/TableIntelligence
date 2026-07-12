# 02 — Where data science helps (nonprofit payoff mapping)

## The master mapping

| Nonprofit question | Method (data-science note) | Deliverable |
|---|---|---|
| "How do our finances trend vs peers?" (public) | Period comparison (03) + forecast (07) | Multi-year 990 trend + efficiency ratios |
| "Who are our best/lapsed donors?" | RFM on donations (04) | Donor segments (major/lapsed/new) + ask lists |
| "Are we keeping donors?" | Retention cohorts (04) | Donor-retention curves by cohort/channel |
| "Which donors will lapse?" | Classification (08) | At-risk donor list + why (09) → targeted re-engagement |
| "What's a donor worth?" | Regression / LTV (08) | Donor LTV to prioritise cultivation |
| "Why did giving drop?" | Key-driver `explain_metric` (09) | Ranked drivers + segments |
| "What will we raise next quarter/year?" | Forecast (07) | Revenue forecast + range for budgeting |
| "Which channels/appeals actually work?" | Association (02) / causal (10) | Channel effectiveness; causal appeal effect |
| "What donor types exist?" | Clustering (05) | Donor personas for tailored campaigns |
| "Did the matching-gift campaign *cause* more giving?" | Causal (10) | Estimated effect + refutation |

## The two flagship deliverables
1. **Public financial teardown (outreach + first report).** From 990s alone: program-expense
   ratio trend, fundraising cost-per-dollar trend, revenue-mix shift, multi-year forecast.
   Zero trust required — the strongest cold-outreach hook of any vertical.
2. **Donor retention & win-back (the retainer).** RFM + retention cohorts + a lapse-risk
   model on their donor CRM. Donor retention is the sector's biggest, least-managed leak, and
   it's structurally identical to e-commerce repeat-rate — you already have the tooling.

## Positioning notes
- **Sell to the consultant/grant-writer** who serves many orgs when you can — they decide
  fast, bill for this, and one relationship multiplies into many orgs' data.
- **Frame as mission-efficiency**, never judgment: "every dollar saved on fundraising is a
  dollar to the program." Efficiency findings touch board politics; lead with the upside.
- **Match to data:** public 990 work needs nothing from them (great sample); donor
  modelling needs a real CRM with history — mid/large orgs, not tiny grant-only shops (the
  volume + budget discipline from `../data science/` and the outreach anti-targets).

## The connective tissue
A nonprofit's donor file behaves like an e-commerce customer file and its 990 like a
financial statement — so your e-commerce toolkit (RFM, cohorts, churn/LTV) transfers almost
directly, and the public-data angle from `../digital marketing/` (teardown before contact)
is stronger here than anywhere else.
