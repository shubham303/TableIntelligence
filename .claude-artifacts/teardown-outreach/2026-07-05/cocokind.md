# Cocokind — Teardown & Outreach

**Date:** 2026-07-05 · **Vertical:** Shopify DTC skincare · **Tier:** retainer (~$1M+/yr) · **Status:** drafted

## Qualification
- **Domain:** cocokind.com · `/products.json` OPEN
- **Founder / contact:** Priscilla Tsai — founder & CEO (About page, wide press). Famously data- & mission-driven; owner-led.
- **Five-signal check:** (1) has data, no visible in-house analyst ✅ · (2) real funded brand, buys tools ✅ · (3) founder public/reachable ✅ · (4) recurring reporting need ✅ · (5) public catalog hook ✅ → **5/5, strong**

## Raw teardown output (deterministic — `shopify_teardown.py`)
```
=== TEARDOWN: https://cocokind.com ===
Products: 87 | Variants: 141 | avg variants/product: 1.62
Price (USD): min 5.0 | median 18.0 | mean 27.92 | max 250.0
  bands: {'<$30': 97, '$30-59': 31, '$60-99': 9, '$100-149': 2, '$150-249': 1, '$250+': 1}
  → Price ladder gap: near-empty $60-149 middle
Sold out but still listed: 24
   - calm & hydrate starter set / cleanse & fade duo / ceramide hydration duo /
     radiant hydration duo / lightweight hydration duo / body cleansing bar /
     best skin ever bundle / turmeric tonic / travel-size ceramide barrier serum /
     advanced retinol gel 0.5%  (…24 total)
Launch cadence: {2014:1,2016:1,2017:1,2018:1,2019:5,2020:5,2021:8,2022:4,2023:17,2024:19,2025:17,2026:8}
Product types: {skincare:45, Bundle:25, merch:11, quiz bundle:5, Gift Card:1}
Tag concentration: 558 unique
```

## Findings (public catalog = hypotheses)
1. **28% of catalog sold out but still listed** — 24 of 87 products have every variant unavailable, pages still live. Many are bundles/duos + a couple of actives (retinol gel 0.5%, turmeric tonic). Ad/search clicks landing there hit dead ends.
2. **Mid price-ladder gap** — variants cluster <$30 (97); only 12 across all bands above $60. Possibly deliberate for an affordable brand, but the usual spot to add a mid-tier set that lifts AOV.
3. **Positive:** relentless, consistent innovation (17–19 launches/yr, three years running) and unusually granular merchandising (558 tags) — the structure that makes the paid sales-data analysis (retention, repeat-buyer drivers) pay off.
- **Public data can't show:** traffic/ad spend hitting the 24 dead pages; whether sub-$30 concentration caps AOV or reflects strategy.

## Draft outreach — cold email
**Subject:** 24 Cocokind pages that can't be bought right now

Hi Priscilla,

Quick flag on Cocokind's catalog: about a quarter of it — 24 products, including several starter sets and duos and a couple of actives like the retinol gel — is listed but shows every variant sold out. Any ads or search pointing there are landing on something no one can buy. Separately, pricing clusters heavily under $30 with very little in the $60–150 range — maybe deliberate, but often where a mid-tier set can lift average order value.

I'm a data scientist who works with e-commerce brands on their sales data; I spotted this just from your public catalog.

To be upfront, that's the simple version — surface structure anyone can see, not your actual sales. The real insight comes from your orders data run through proper analysis (personal info stripped, I only need the numbers): which of those sold-out pages still draw traffic, what actually drives repeat purchases, and where AOV leaks — the kind of thing public data physically can't show.

Here's how I work: I'll share a sample report so you can see the quality and the kind of insight it surfaces. If you like it, the full analysis on your real data is a paid report from there.

Just reply and I'll send the sample over.

Best,
[Shubham Randive](https://www.linkedin.com/in/shubham-randive-303/)

## Pre-send checklist
- [ ] Spot-check a few sold-out pages live (may be restocked)
- [ ] Find direct address (firstname@ / About / press) — not info@
- [ ] Fill signature (email + proof link)
- [ ] Send by hand · log in index.md · follow up ~day 4–5
