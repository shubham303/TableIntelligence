# Nonprofits for a data scientist — the map

Nonprofits are a **secondary but distinctive** target: they have the **richest public data
of any vertical** (US IRS Form 990s are fully public), a genuine recurring reporting need
(grant/impact reports), and a mission pull that makes outreach warmer. The catch: small orgs
have thin budgets, so aim at **mid-to-large orgs ($1M+ budgets)** and the **consultants/grant
writers** who serve many of them.

## Read in this order
| # | File | What you'll get |
|---|------|-----------------|
| 01 | data-and-metrics | Form 990 public data + donor/fundraising metrics. |
| 02 | where-data-science-helps | Each nonprofit problem → the algorithm → the deliverable. |

## The three things to hold onto
1. **Public 990 data is a teardown superpower.** Unlike any other vertical, you can produce
   a legitimate financial analysis of a US nonprofit *before contact, with zero trust
   required* — multi-year revenue, expenses, program-expense ratio, fundraising efficiency,
   exec comp — from ProPublica's Nonprofit Explorer or Candid. Great for outreach hooks.
2. **The recurring need is reporting to funders.** Grant reports, impact reports, and board
   decks are deadline-driven, high-stakes, and repeat every cycle — because *funding depends
   on them*. That's the wedge and the retainer.
3. **Budget is real but committee-driven and mission-guarded.** Spending on "overhead"
   (analytics) is politically sensitive for boards/donors, so target orgs with genuine
   budgets and, ideally, the **consultants** who bill for this work and decide faster.

## The mental model
> A nonprofit **raises** money (donors, grants, events), **spends** it on programs, and must
> **report impact** to keep the money flowing. Your job is to make the raising more
> efficient and the reporting rigorous — both are data problems.

## Guardrails specific to this vertical
- **Sensitive data.** Individual donor records are PII and politically sensitive — handle
  like customer PII (strip it; work on aggregates). Early on, prefer public/aggregate data.
- **Frame findings with care.** "Fundraising cost per dollar rose" is true and useful but
  touches a nerve; present as an efficiency opportunity, never a judgment.
