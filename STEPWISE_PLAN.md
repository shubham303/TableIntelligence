# Table Intelligence — Stepwise Product Plan (reconciled)

_Merges the capability/trust product strategy (normalization contract, honesty seam,
blast-radius sequencing) with what's **already built** in `tabint`. Companion to:_
- `PRODUCT_PLAN.md` — locked decisions + infra architecture.
- `IMPLEMENTATION_PLAN.md` — granular build checklist (the plumbing).
- This file — the **product/strategy roadmap**, sequenced by what's actually left.

## Thesis (adopted)
A **capability product, not a convenience product.** You sell inference the native dashboards
structurally can't do (association now, causal later), across a business's sources, from one
plain-English question — run locally, data never leaves the machine. Because the buyer pays
*because they can't do it themselves*, they also can't verify it: **this is a trust product**,
and trust (not breadth) is the retention mechanism.

## Where you actually are (inventory, 2026-07-19)
- ✅ **Data-science engine exists** — `tabint`, 44 deterministic MCP tools: descriptive
  (`profile`, `compare_periods`, `decompose`), cohorts/retention (`retention_cohorts`, `rfm`),
  **association (`market_basket`)**, **causal (`causal_effect`, DoWhy + refutation)**, ML
  (`train_classifier/regressor`, `feature_importance`, SHAP), forecasting, changepoints.
- ✅ **Entitlement/gating** — `entitlement.py` (validate-key client, 2-device cap, fail-open,
  `@requires_paid`), `account_status` tool, tested.
- 🟡 **Backend** — Neon (DB) + Vercel functions + Stripe; migration ready, awaiting Neon project.
- 🟡 **Packaging** — branded console scripts; publish + `.mcpb` pending.
- ❌ **Honesty seam** — tools emit method/assumptions/params, but NOT a uniform trust score +
  decline-to-answer. **The #1 gap.**
- ❌ **Normalization contract** — no canonical schema for connectors to target yet.
- ❌ **Connectors** — none. ❌ **Website product page / docs / billing UI.**

**Implication:** don't "re-prove the engine." Re-sequence around the seams, connectors, and GTM.

## Two invariants to install NOW (before connector #2)
- **a) Normalization contract** — the canonical table shape every source normalizes into before
  analysis. `tabint` tools already consume a table; formalize the target shape so a connector
  (built) or a first-party MCP server (delegated) just has to emit it. Cheap now, load-bearing later.
- **b) Honesty seam** — every result carries *how much to trust it* + a *refusal* when the data
  can't support the question. Retrofit a uniform envelope across the 44 tools while stakes are low,
  so it's habitual by the time causal answers cost real money. Humility installed while cheap.

---

## Reconciled phases (sequenced by blast radius AND by what's left)

### Phase A — Make the existing engine sellable + trustworthy  ← START HERE
The engine is done; wrap it for trust and distribution.
- **A1. Honesty seam across all 44 tools** — ✅ **DONE (2026-07-19)**. Infra: `honesty.py`
  (`Trust` + `TrustLevel` + `decline`/`from_sample_size`/`combine`/`with_caveats`), `Result.trust`,
  `result_dict` emits a uniform `trust` block + `declined` on EVERY tool (default `unassessed` —
  never a fake `high`); MCP instructions surface it. **All 13 analytics modules retrofitted** with
  real confidence + method-specific caveats, and decline-to-answer where the data can't support the
  method: causal (<50 rows / no treatment variation / failed placebo refutation, never `high`),
  forecast/decompose (short history / <2 seasonal periods), classifier/regressor (<30 rows /
  single-class / rare-class), market_basket (too few baskets), rfm/retention (too few customers /
  no repeat data), analyze_association (<10 usable rows; constant column answered definitively, not
  declined), cluster (<2 rows). Deterministic transforms (feature_computation) = `high` "not an
  estimate". Callers (`workspace`, `mcp_server._train`) guard the new declined-`Result` path.
  **200 tests pass**; every `Result` return verified to carry `trust`.
- **A2. Normalization contract** — ✅ **DONE (2026-07-19)**: `connectors/contract.py` defines
  canonical entities (`payments`, `customers`, `subscriptions`, `invoices`) + `conform(df, entity)`
  (exact columns/order/dtypes; amounts in major units, tz-aware timestamps). Connectors emit these;
  the 44 analytics tools consume them unchanged.
- **A3. Finish plumbing** (from `IMPLEMENTATION_PLAN.md` Phase 0): Neon schema, validate-key
  Vercel fn, Stripe $5/mo + 3-day trial, publish + install on Claude Desktop/Code.
- **A4. Ship the free tier** — local CSV/Excel → existing analysis **with trust signals**.
- _Exit:_ a real messy CSV → analysis a business owner calls useful, with trust signals; a paying
  trial user installed end-to-end.

### Phase B — First connectors (into the contract)
- **B1. Stripe end-to-end** — ✅ **DONE (2026-07-19)**. Connector framework (`connectors/base.py`
  registry + `Connector` ABC + `materialize`), `connectors/stripe.py` (direct REST via `urllib`,
  cursor pagination, cents→units, epoch→UTC → the contract). MCP tools: `connect_stripe` (**paid**,
  `requires_paid`, BYO `STRIPE_API_KEY`, data fetched machine→Stripe only), `list_connectors`
  (free), and a `stripe` platform prompt. E2E verified: connect → canonical tables → rfm/profile
  run with the honesty envelope. 7 connector tests; 207 total pass.
- **B2. One direct-credential source** (Postgres/MySQL/SQLite/Google Sheets) — paste a connection
  string; no OAuth, no website. Exercises the contract across two very different sources.
- **Keep credential handling out of connector logic** (env/config now → OAuth later is config,
  not a rewrite). OAuth-brokering website deferred (see PRODUCT_PLAN Phase 2).
- _Exit:_ connect a real Stripe + one DB/Sheet; pull → normalize → analyze each.

### Phase C — Cross-platform association
- Host (Claude) routes each question to the platforms where it's meaningful; `market_basket` +
  association tools run per-source; results consolidated *for presentation*, each traceable to one
  source. Association is the middle rung — genuine insight, **no causal claim, low blast radius**.
  Carry real value here while earning confidence for causal.
- _Exit:_ 3+ sources → useful cross-platform associations from plain-English questions.

### Phase D — Causal, done deeply and trustworthily on ONE platform (the moat)
- `causal_effect` (already built) applied **safely, automatically, legibly** — with the honesty
  seam doing the heavy lifting: **decline-to-answer when observational data can't support a causal
  claim** (no treatment variation, too few obs, no counterfactual). Surface assumptions in
  business language ("so, raise the price or not?"). Depth-done-trustworthily > breadth-done-
  confidently-wrong.
- _Exit:_ one causal question answered correctly on messy real data — *including correctly
  declining* when it can't.

---

## Cross-cutting decisions to make deliberately
1. **Buyer: non-technical owner vs. technical interpreter** (their §4). Your outreach targets
   non-technical owners → the honesty seam's *translation layer* becomes as much the product as the
   algorithm. Lean non-technical, and budget for the translation work. **Decide before Phase D.**
2. **Pricing: $5 (locked) vs the doc's $20.** The capability framing genuinely supports more than
   $5. Keep $5 as default (simplicity/low-needs), but **run the WTP conversation with real owners
   before finalizing** — don't anchor either number blind. Hold loosely.
3. **Build vs. delegate, per source** — wire one source through its first-party MCP server end-to-
   end; if the data isn't analysis-ready, you need a shim regardless (which is most of a connector).

## Validation — use the pipeline you already have
The **50-company outreach list** (`.claude-artifacts/teardown-outreach/2026-07-18/`) IS your
design-partner + first-100 WTP pool. Before/alongside building: ask 3–5 of them what they do today
to answer these questions, how painful it is, what they'd pay. Watch the flinches.

## Deliberately NOT building yet (their §7, endorsed)
OAuth-brokering website/token vaults · streaming/sampling/query-in-place · warehouse connectors
(Snowflake/BigQuery) · server-side storage of anything sensitive · **causal before the honesty
seam + association layer are solid.**

## Next 2–4 weeks (concrete)
1. **Honesty-seam envelope** (A1) — spec `{result, confidence, caveats, declined}` + retrofit the
   descriptive tools. This is the highest-leverage thing on the whole list.
2. **Normalization contract** (A2) — write it down; make one existing tool consume it.
3. **Finish Phase 0 plumbing** (A3) — Neon + validate-key + Stripe trial + install (in progress).
4. **Stripe connector end-to-end** (B1) with a test-mode key.
5. **One direct-credential source** (B2).
6. **One cross-source association** (C) — prove the middle-rung value before touching causal.
7. **Talk to 3–5 owners from the outreach list** — WTP + which sources they want.
