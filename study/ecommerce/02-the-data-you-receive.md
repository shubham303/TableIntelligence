# 02 — The data an e-commerce client actually hands you

The bridge from "store" to "CSV on your desk." Know these shapes cold so you can scope an
engagement the moment you see the export.

## The core tables
1. **Orders / order-lines** (the crown jewel). Two common shapes:
   - **Order-lines (tidy):** one row per item per order — `order_id, customer_id,
     order_date, product/sku, quantity, unit_price`. This is what Online Retail II and the
     basket/RFM functions expect. **Prefer this shape.**
   - **Order-level:** one row per order with a total. Fine for AOV/cohorts, but you lose
     product-level analysis (no basket).
2. **Customers** — `customer_id, first_order_date, location, acquisition_channel`,
   sometimes email/name (**PII — tell them to strip it**). Watch the id: use a *stable*
   customer id across orders, not a per-order one (Olist's `customer_unique_id` trap).
3. **Products / catalog** — `sku, title, category, cost, price`. On Shopify, the public
   `/products.json` gives catalog + price bands without any private data (your teardown hook).
4. **Sessions / traffic (GA4)** — behavioural: sessions, source/medium, device, landing
   page, conversions. Join to orders on date/campaign for funnel analysis.
5. **Marketing exports** — Google/Meta Ads spend, Klaviyo email events. Join for CAC/ROAS
   and channel attribution.

## Where the data lives (platforms)
- **Shopify** (dominant for DTC) — admin exports, the Analytics API, and public
  `/products.json`. Most of your DTC prospects are here.
- **WooCommerce / Magento / BigCommerce** — SQL/CSV exports.
- **Amazon / marketplaces** — seller reports; more restricted, less public.
- **Klaviyo / GA4 / Google Ads** — the surrounding marketing data (see `../digital
  marketing/03`).

## The messiness to expect (and the first-pass fix)
Real e-commerce exports are dirty — plan for it (data-science note 01 = your cleanup pass):
- **Cancellations/refunds** as negative quantity or separate rows (Online Retail II: invoices
  starting `C`). Decide whether to net them out — it changes every total.
- **Missing customer ids** (~20% in Online Retail II) — guest checkouts; drop for
  customer-level analysis, keep for product-level.
- **Mixed currencies / test orders / bot traffic** — filter before aggregating.
- **Timezones** on timestamps — matters for daily/cohort boundaries.
- **Skew** — a few whales dominate; medians and outlier flags keep numbers honest.

## The scoping reflex
- Have a clean **order-lines + customers** table with enough history (thousands of orders,
  months of dates)? → the full ladder: RFM, cohorts, basket, forecasting, LTV.
- Only an **order-level** export or a few hundred orders? → stay descriptive/diagnostic:
  AOV, repeat-rate, RFM, "what changed." Don't promise ML/forecasting the data can't support
  (the volume discipline from `../data science/`).

## PII guardrail (non-negotiable)
Never keep customer emails/names/addresses. You analyse **behaviour and money**, not
identities. Tell the client to strip PII from any export before they send it — it protects
them and you, and it's a trust signal on the first call.
