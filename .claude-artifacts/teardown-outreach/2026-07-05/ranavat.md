# Ranavat — Teardown & Outreach

**Date:** 2026-07-05 · **Vertical:** Shopify DTC skincare (luxury Ayurvedic) · **Tier:** retainer (~$1M+/yr) · **Status:** drafted

## Qualification
- **Domain:** ranavat.com · `/products.json` OPEN
- **Founder / contact:** Michelle Ranavat — founder & CEO (About page, press). Brand's public face; clear decision-maker.
- **Five-signal check:** (1) data, no visible analyst ✅ · (2) luxury price points = margin to pay ✅ · (3) founder is the brand ✅ · (4) recurring reporting ✅ · (5) public catalog hook ✅ → **5/5**

## Raw teardown output (deterministic — `shopify_teardown.py`)
```
=== TEARDOWN: https://ranavat.com ===
Products: 70 | Variants: 170 | avg variants/product: 2.43
Price (USD): min 0.98 | median 38.51 | mean 60.58 | max 500.0
  bands: {'<$30': 73, '$30-59': 41, '$60-99': 29, '$100-149': 11, '$150-249': 11, '$250+': 5}
Sold out but still listed: 1
   - Renewing Leave In Treatment Mini (15mL)
Launch cadence: {2017:2,2018:2,2019:4,2020:5,2021:5,2022:3,2023:9,2024:8,2025:14,2026:18}
Product types: {Skincare:29, Gift Set:17, Fragrance:9, Haircare:8, Accessory:5, Insurance:1, Gift Cards:1}
Tags: spo-default:45, no-returns:41, ge-back-order:29, set:22, mini:17, fragrance:11, ...
```
> Note: min $0.98 is a shipping-insurance widget, not a product — ignore as a price point.

## Findings (public catalog = hypotheses)
1. **Accelerating launch velocity** — new products/yr climbed from ~5 (2020–21) to 14 in 2025 and **18 already in 2026** (half a year in). Growth signal, but the point where new launches can cannibalize hero serums or splinter focus.
2. **~24% of catalog is gift sets/bundles** — 17 of 70 products are Gift Sets. Bundles lift AOV but can discount buyers who'd pay full price; incremental-vs-cannibalized split is worth knowing.
3. **Positive:** cleanest catalog of the batch — only 1 sold-out-but-listed, healthy 2.4 variants/product (no fragmentation), well-distributed price ladder from entry minis to a $500 hero.
- **Public data can't show:** whether 2025–26 launches are additive or cannibalizing; true margin contribution of the gift-set strategy.

## Draft outreach — cold email
**Subject:** Ranavat's 2026 launch pace — additive or cannibalizing?

Hi Michelle,

Ranavat's launch pace has climbed steeply — 14 new products in 2025, 18 already in 2026, plus gift sets at ~a quarter of the catalog — which is great for growth but also exactly where new SKUs can quietly cannibalize your hero serums or bundles discount buyers who'd have paid full price. I spotted that just from your public catalog; whether those launches are actually additive (and what the gift sets add vs. cannibalize) only shows up in your orders data.

I'd love to send you a short sample teardown so you can see what that looks like — free, and the full report on your real numbers is only paid if it's useful. Let me know!

[Shubham Randive](https://www.linkedin.com/in/shubham-randive-303/)

## Pre-send checklist
- [ ] Sanity-check gift-set count / recent launches live
- [ ] Find direct address — not info@
- [ ] Fill signature (email + proof link)
- [ ] Send by hand · log in index.md · follow up ~day 4–5
