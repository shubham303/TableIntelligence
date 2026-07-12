# 03 — The analytics stack & the data you'll actually receive

This note is the bridge between "marketing concepts" and "a CSV on your desk." It covers
the tools that hold the data, what each export looks like, and the one hard idea that runs
through all of them: **attribution**.

## The tools (and the table each produces)
- **Google Analytics 4 (GA4)** — the site's behavioural spine. Event-level: one row per
  event (`page_view`, `add_to_cart`, `purchase`) with `user_pseudo_id`, session, traffic
  source (source/medium/campaign), device, geo, and e-commerce revenue. Exported via the
  GA4 UI, BigQuery link, or API. *This is the single most common table a client hands an
  agency.* (You downloaded the GA4 BigQuery sample to study its real shape.)
- **Google Search Console (GSC)** — organic search performance: query × page × date →
  impressions, clicks, CTR, position. The SEO client's core file.
- **Google Ads** — paid search: campaign/ad group/keyword × date → cost, clicks,
  impressions, conversions, conversion value. Dense daily numeric data.
- **Meta / LinkedIn Ads Manager** — paid social, same idea by campaign/adset/creative.
- **CRM / e-commerce platform** (Shopify, HubSpot, Klaviyo, a SQL DB) — the **orders and
  customers** tables: the ground truth of who bought what, when, for how much. This is
  where RFM, cohorts, basket, and LTV live.
- **Looker Studio / Tableau / Power BI** — *visualization* layers on top of the above. Note:
  these are dashboards, **not** analysis. Clients have these already; they are your
  competition-that-isn't, because they show numbers without explaining them.

## What "getting the data" really means
Clients rarely hand over a clean single CSV. Expect:
- **Multiple exports** that must be joined (GA4 sessions + Google Ads spend + orders) on
  keys like date, campaign, or customer id — the Olist dataset you downloaded is
  deliberately this multi-table shape.
- **Messiness** — missing customer ids, cancellations as negatives, mixed currencies,
  timezone mismatches, sampled GA4 data. (Data-science note 01 is your first-pass cleanup.)
- **PII** — real customer emails/names. Your guardrail: tell them to strip it; you work on
  behaviour and money, not identities.

## Attribution — the one concept to genuinely understand
**Attribution = deciding which channel/touch gets credit for a conversion** when a customer
touched several. It's the central, disputed problem of marketing analytics.
- **Last-click** — 100% credit to the final touch. Simple, default, and *wrong* — it
  over-credits bottom-funnel (brand search, email) and starves awareness channels.
- **First-click** — all credit to the first touch. The opposite bias.
- **Linear / time-decay / position-based** — spread credit across touches by various rules.
- **Data-driven attribution (DDA)** — model the incremental contribution of each touch.
Why you care: attribution is *fundamentally a causal question* ("what did this channel
actually *cause*?") wearing a reporting costume. Rule-based models are heuristics; the
honest version is causal inference (data-science note 10). When a client argues about which
channel "worked," you can offer the rigorous answer instead of a heuristic — that's senior
positioning.

## The gap you're selling into (say this out loud on calls)
The stack above is excellent at **collecting and displaying** data and useless at
**interpreting** it. Every tool answers "what are the numbers?"; almost none answer:
- *Why* did the metric change? → note 09
- *What* will it be next quarter? → note 07
- *Who* will churn / convert? → note 08
- Did our work *cause* the result? → note 10
That interpretation layer is your entire product. You are not competing with GA4 or Looker;
you sit on top of them.
