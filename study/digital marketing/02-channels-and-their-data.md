# 02 — The channels & the data each one emits

A "channel" is a route to the customer. Each has its own jargon, its own success metric,
and — what you care about — its own **data export shape**. This is the note that tells you
what a client will actually send you.

## SEO (Search Engine Optimisation) — organic search
**What it is:** earning free traffic by ranking in Google's unpaid results. Slow, compounding,
no per-click cost. The core discipline of agencies like Artemis.
**They obsess over:** keyword rankings, organic sessions, impressions, click-through rate
from search, backlinks, "domain authority", Core Web Vitals (page speed).
**Data it emits:**
- **Google Search Console** — per-query and per-page: impressions, clicks, CTR, average
  position, by date. This is the SEO client's core table.
- **GA4** — organic sessions, landing pages, conversions from organic.
- Rank-tracker exports (keyword → position over time).
**Your hooks:** ranking→revenue gap (rankings up but conversions flat → note 09);
traffic trend vs seasonality (note 07 decompose); changepoint at an algorithm update
(note 07); which pages/queries drive conversions (note 09).

## PPC / Paid Search (Google Ads) — pay-per-click
**What it is:** buying top-of-search placement, paying per click. Fast, controllable,
stops the moment you stop paying. SUMOBLUE's whole business.
**They obsess over:** CPC, CTR, conversion rate, **ROAS**, quality score, cost per
conversion, wasted spend.
**Data it emits:**
- **Google Ads export** — per campaign/ad group/keyword/day: impressions, clicks, cost,
  conversions, conversion value. Rich, daily, numeric — ideal for your engine.
- Merchant Center / Shopping feeds for e-commerce.
**Your hooks:** which campaigns/keywords actually drive profit (note 09); daily spend
efficiency trend + changepoints (note 07); "does more spend *cause* more conversions or
just correlate?" (note 10); forecast next quarter's spend/return (note 07).

## Paid Social (Meta, LinkedIn, TikTok Ads)
**What it is:** paid ads on social platforms, targeted by audience rather than search
intent. Great for awareness and retargeting.
**They obsess over:** CPM, CTR, CPA, ROAS, audience/creative performance, ad fatigue.
**Data it emits:** per campaign/adset/creative/day: spend, impressions, clicks,
conversions, by audience. Similar shape to Google Ads.
**Your hooks:** creative/audience A-B effects (note 10 if randomised, else note 03);
diminishing returns / fatigue as a changepoint (note 07).

## Email / CRM / Lifecycle (Klaviyo, HubSpot, Mailchimp)
**What it is:** owned marketing to a list you already have — newsletters, automated flows
(welcome, abandoned-cart, win-back). No media cost, highest ROI channel. Magnet Monster's
specialty.
**They obsess over:** open rate, click rate, conversion rate, revenue per email, list
growth, unsubscribes, **flow vs campaign revenue**.
**Data it emits:** per-send and per-subscriber event logs (sent/opened/clicked/purchased),
plus the underlying customer + order tables. **This is the richest data for your
highest-value work.**
**Your hooks:** RFM segmentation for targeting (note 04); retention cohorts behind the
"email revenue" headline (note 04); churn/win-back prediction (note 08); send-time or
subject-line effect testing (note 02/03); "does email engagement *cause* repeat purchase?"
(note 10).

## Organic Social & Content
**What it is:** unpaid posting/content to build audience and trust. Hard to attribute,
slow. (This is also *your own* credibility channel — see the outreach skill.)
**Data it emits:** engagement metrics per post; weak conversion attribution. Least
data-science-rich; usually a supporting story, not the main analysis.

## The cross-channel truth
Real customers touch **several channels** before buying (see an ad, later Google the brand,
then click an email). This is why **attribution** (note 03) is hard and disputed — and why
the causal question (data-science note 10) is where the senior value sits. No single
channel's dashboard sees the whole journey; stitching them is a service, not a tool.
