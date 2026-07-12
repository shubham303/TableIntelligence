# 01 — Nonprofit data & metrics

## The public data (the vertical's superpower)
**IRS Form 990** — every US tax-exempt org files one, and it's fully public:
- **Revenue** by source (contributions, grants, program service, investment), multi-year.
- **Expenses** split into **program / management / fundraising** — the basis of efficiency
  ratios.
- **Net assets**, executive compensation, largest contractors.
Sources: **ProPublica Nonprofit Explorer**, **Candid/GuideStar**. Multi-year filings let you
build a legitimate trend analysis (data-science notes 03, 07) with nothing asked of the org.

## The metrics that matter
**Efficiency / stewardship**
- **Program-expense ratio** = program expenses ÷ total expenses. The headline "how much goes
  to the mission" number donors and watchdogs (Charity Navigator) watch. A multi-year slip
  is a real, hook-worthy finding.
- **Fundraising efficiency** = dollars raised ÷ fundraising dollars spent (or its inverse,
  **cost per dollar raised**). Is fundraising getting more or less efficient?
- **Administrative-expense ratio.**

**Fundraising / donor (needs their internal data)**
- **Donor retention rate** — % of donors who give again (the sector's biggest leak; often
  ~40–45%). This is a **retention/cohort** problem (data-science note 04) identical in shape
  to e-commerce repeat-rate.
- **Donor LTV**, **average gift**, **recurring vs one-time**, **lapsed donors**.
- **Acquisition cost per donor**, **channel performance** (direct mail, email, events,
  grants).
- **RFM on donors** — Recency/Frequency/Monetary works directly on donation history (note
  04); "major donor," "lapsed," "new" segments drive very different asks.

**Program / impact**
- Outcomes per dollar, beneficiaries served, cost per outcome — the substance of impact
  reports (often messier, org-specific data).

## The data you'll receive
- **Public:** 990s (structured financials), annual reports.
- **Internal (once engaged):** donor CRM exports (Salesforce Nonprofit, Bloomerang,
  DonorPerfect) — `donor_id, gift_date, amount, campaign, channel`; grant pipelines; program
  outcome trackers. The donor-gift table is structurally an order-lines table — RFM and
  cohorts apply unchanged.

## Traps to spot
- **Overhead-ratio obsession** — the sector over-indexes on program-expense ratio; a
  too-low overhead can *starve* capacity. Present ratios as context, not verdicts.
- **Restricted vs unrestricted funds** — not all revenue is spendable; don't read total
  revenue as available budget.
- **Seasonality** — year-end/giving-season spikes dominate; decompose (note 07) before
  reading trends.
