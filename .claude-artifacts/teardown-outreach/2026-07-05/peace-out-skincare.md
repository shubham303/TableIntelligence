# Peace Out Skincare — Teardown & Outreach

**Date:** 2026-07-05 · **Vertical:** Shopify DTC skincare (acne) · **Tier:** retainer (~$1M+/yr) · **Status:** drafted

## Qualification
- **Domain:** peaceoutskincare.com · `/products.json` OPEN
- **Founder / contact:** Enrico Frezza — founder & CEO (About page, press). Founder-run.
- **Five-signal check:** (1) data, no visible analyst ✅ · (2) real brand, buys tools ✅ · (3) single clear founder-CEO ✅ · (4) recurring reporting ✅ · (5) public catalog hook ✅ → **5/5**

## Raw teardown output (deterministic — `shopify_teardown.py`)
```
=== TEARDOWN: https://peaceoutskincare.com ===
Products: 61 | Variants: 68 | avg variants/product: 1.11
Price (USD): min 0.01 | median 28.0 | mean 29.9 | max 112.0
  bands: {'<$30': 46, '$30-59': 18, '$60-99': 2, '$100-149': 2, '$150-249': 0, '$250+': 0}
Sold out but still listed: 13
   - Puffy Eyes / Acne Routine Kit (CAN) / Intense Defense Kit (CAN) /
     Daily Defense Kit (CAN) / Acne Day & Night Duo (CAN) / Acne Serum (UNI) /
     Acne Gel Cleanser (CAN) / Retinol Eye Lift Patches (CAN) /
     Pore Perfecting Cleanser (CAN) / Puffy Eyes (CAN)  (…13 total)
Launch cadence: {2017:1,2018:1,2019:3,2020:2,2021:1,2022:3,2023:8,2024:29,2025:7,2026:6}
Product types: Acne Treatments & Kits:7, Cleanser:5, Hydrocolloid Patches:5, ...
Tags: Gratis:50, Active SKUs:46, Acne:36, Subscription:27, UNI-SKU:23, CAN-SKU:21, US-SKU:11, ...
```

## Findings (public catalog = hypotheses)
1. **Regional SKUs duplicated as separate products; the Canadian set is mostly dead** — CAN/UNI/US versions listed as distinct products; 13 sold-out-but-still-listed, nearly all `(CAN)`. Dead pages + SEO clutter competing with live US listings.
2. **A 2024 launch spike worth pruning** — 29 launches in 2024 (vs 6–8 around it), same period as the regional split; check whether new SKUs earn shelf space or dilute the hero acne line.
3. **Positive:** subscription infrastructure already built (27 products tagged Subscription) and bestsellers clearly flagged — the recurring-revenue engine exists; the best foundation for the paid deep-dive (cohort retention, churn drivers).
- **Public data can't show:** which regional pages still draw traffic; whether 2024 SKUs add revenue or cannibalize.

## Draft outreach — cold email
**Subject:** Peace Out's Canadian pages are mostly unbuyable

Hi Enrico,

Quick flag on Peace Out's catalog: you list regional versions of products (CAN / UNI / US) as separate items, and 13 of them show sold out but still live — nearly all the Canadian ones. Those act as dead ends and quietly compete with your live US listings in search. There was also a big burst of new SKUs in 2024 that might be worth pressure-testing against your hero acne line.

I'm a data scientist who works with e-commerce brands on their sales data; I spotted this just from your public catalog.

To be upfront, that's the simple version — catalog structure, not real sales. The real insight comes from your orders data run through proper analysis (export with personal info stripped, just the numbers): which SKUs actually pull their weight, how your subscription cohort retains, and where the 2024 expansion helped vs. cannibalized — none of which public data can reveal.

Here's how I work: I'll share a sample report so you can see exactly what you'd get. If you like it, the full analysis on your real data is a paid report from there.

Reply and I'll send the sample over.

Best,
[Shubham Randive](https://www.linkedin.com/in/shubham-randive-303/)

## Pre-send checklist
- [ ] Confirm CAN pages still sold out live
- [ ] Find direct address — not info@
- [ ] Fill signature (email + proof link)
- [ ] Send by hand · log in index.md · follow up ~day 4–5
