# Table Intelligence — Implementation Plan (single source of truth)

Step-by-step build checklist. **Resumable:** each step is a checkbox; update it the moment a step
is done and add a line to the Progress Log. To resume after a break: read the Progress Log, find
the first unchecked step, continue. Strategy/decisions live in `PRODUCT_PLAN.md` — this file is
the "how + track."

## Repos & locations
- **Analytics + MCP server** — `/Users/shubhamrandive/Documents/codes/TableIntelligence` (import pkg `tabint`).
- **Control plane** — layered Python package `control-plane/tabint_control/` (repository → service
  → endpoint + factory/facade). **DuckDB locally, Postgres/Neon in prod** (chosen by env). Stripe
  for payments. _(Supabase dropped 2026-07-19; DuckDB-local added so dev needs no accounts.)_
- **Website + docs + app + prod endpoints** — `/Users/shubhamrandive/Documents/codes/shubham-site`
  (Astro on Vercel). This is the **endpoint/web layer**: docs, pricing, payments, account/metadata,
  data access, and the validate-key/Stripe endpoints (which reuse the control-plane services).
- **Deferred account/deploy steps** — `steps_for_shubham.md` (Neon, Stripe, Vercel, PyPI).
- **Reference** — sibling `stripe-insights-mcp` for the Stripe connector.

## Locked decisions (from PRODUCT_PLAN.md)
Python-only · name **Table Intelligence** · **$5/mo flat** · freemium: free core tier + **3-day trial** →
paid · **connectors + cloud artifact storage = paid-only** · **2-device cap** · single server, many
connectors + platform prompts · raw data never leaves the machine.

---

## Phase 0 — Foundations: one paid user, end-to-end, on 2 hosts

### 0.1 Packaging the server for public distribution  🟡 (in-repo done; publish pending)
- [x] Console scripts `table-intelligence` + `table-intelligence-mcp` added (aliases of `tabint`/`tabint-mcp`); both register on `uv pip install -e .`.
- [x] Keywords added to `pyproject.toml`.
- [ ] **At publish time:** decide PyPI dist name (`table-intelligence` vs keep `tabint`) — changing `name` touches `uv.lock`, do it in the publish PR.
- [ ] **At publish time:** remove `"Private :: Do Not Upload"` classifier (held now to prevent accidental upload) + add URLs.
- [ ] Verify clean install in a fresh venv: `uvx --from table-intelligence table-intelligence-mcp` starts a stdio server.
- [ ] Smoke test: `create_session` on a sample CSV → `profile` returns.

### 0.2 Entitlement / auth client in the server  ✅
- [x] New module `src/tabint/entitlement.py`: reads `TABINT_API_KEY` + device-id, calls control-plane `validate-key`, caches tier (`trial|paid|free|expired`) with a 6h re-check. Fails open to **free** on error, never crashes. Stdlib-only (urllib).
- [x] Device id helper — persisted uuid in `~/.tabint/device`, ephemeral fallback.
- [x] Unit tests with the endpoint mocked (`tests/test_entitlement.py`, 10 passing).
- [x] Free `account_status` tool added to `mcp_server.py` so users can see their tier.

### 0.3 Free vs paid gating in `mcp_server.py`  ✅
- [x] Tag tools free/paid — all 44 current tools free; paid surface (connectors/artifacts) will use the decorator below.
- [x] `@requires_paid` decorator in `entitlement.py`: returns a clear "upgrade at shubhamrandive.com" result when not entitled (never crashes). Tested.
- [x] Classify the full existing tool list into the free set (recorded in §Tool split — all 44 free).

### 0.4 Control plane — layered, DuckDB local / Postgres-Neon prod  ✅ (local); prod deploy → steps_for_shubham.md
Built as an installable package `control-plane/tabint_control/` with **strict repository → service
→ endpoint layering + a factory/facade** that hides the DB:
- [x] **DB facade** (`db/database.py`): `Database` ABC + `DuckDBDatabase` + `PostgresDatabase`
  (`?`→`%s`). The only code that knows a driver.
- [x] **Factory + facade** (`db/factory.py`): `create_provider()` reads env → right `Database` →
  `RepositoryProvider`. Services stay DB-agnostic.
- [x] **Repositories** (one per table, access only): `users`, `api_keys`, `devices`, `subscriptions`.
- [x] **Services** (logic only): `EntitlementService` (resolve + 2-device cap), `AdminService`
  (mint/set-tier/list).
- [x] **Endpoint**: `cli.py` (`init`/`mint`/`set-tier`/`list`/`resolve`). Prod endpoints = shubham-site.
- [x] **Client wired**: `entitlement.py` local mode resolves via the service against local DuckDB;
  HTTP in prod. `account_status` shows tier + mode.
- [x] Tests: `tests/test_control_plane.py` + local-mode test — **17 passing**. Full flow demoed
  (mint→paid, device cap→device_limit, no key→free).
- [ ] **PROD (steps_for_shubham.md):** create Neon → set `DATABASE_URL`; deploy validate-key +
  Stripe endpoints on shubham-site; point client `TABINT_CONTROL_PLANE_URL` at it.
- [ ] `issue-key` (built in 0.5 with Stripe).

### 0.5 Stripe billing (test mode)  ⬜
- [ ] Stripe product **Table Intelligence** + $5/mo price + **3-day trial** on the subscription.
- [ ] `create-checkout-session` Edge Function (or Astro API route).
- [ ] `stripe-webhook` Edge Function → sync `subscriptions` + flip key tier on `checkout.session.completed`, `customer.subscription.updated/deleted`, trial end.
- [ ] Billing Portal link for cancel/update.

### 0.6 Install on Claude Desktop + Claude Code  ⬜
- [ ] Manual config verified on **Claude Desktop** (`claude_desktop_config.json` with `uvx` command + `TABINT_API_KEY` env).
- [ ] Verified on **Claude Code** (`claude mcp add`).
- [ ] **✅ Phase 0 exit:** test user checks out (trial) → gets key → installs on both hosts → key validates → runs a local analysis. Record the run in Progress Log.

---

## Phase 1 — Launchable product (website + docs + first connector)

### 1.1 Website product page  ⬜
- [ ] `shubham-site`: `/table-intelligence` landing (what it is, privacy/reproducible/defensible, $5/mo, CTA).
- [ ] Nav split so **Services** (consulting) and **Product** (Table Intelligence) are distinct paths.

### 1.2 Multi-host install guides (each verified end-to-end)  ⬜
- [ ] Claude Desktop (one-click `.mcpb` + manual JSON) · Claude Code (`claude mcp add`) · Claude Cowork · Codex (`config.toml`) · Cursor/Windsurf (`mcp.json`) · generic stdio JSON.
- [ ] Each: prerequisites, config block, where the key goes, a "verify it works" command, troubleshooting.

### 1.3 `.mcpb` one-click bundle for Claude Desktop  ⬜
- [ ] Build + test the bundle install on a clean machine.

### 1.4 Docs site  ⬜
- [ ] New Astro content collection `docs` (or `/docs` section): what/why · architecture (diagram from PRODUCT_PLAN) · full tool reference · quickstart · recipes (RFM, forecast, churn, cohorts) · **data-handling & privacy** page · limits.

### 1.5 First connector: Google Sheets (BYO-credentials, paid)  ⬜
- [ ] `src/tabint/connectors/` framework: base class (fetch client + optional OAuth hook + platform prompt) + registry gated by entitlement.
- [ ] `connectors/google_sheets.py`: pull a sheet → local table (user pastes a service-account key or uses a shared-link fetch). Paid-gated.
- [ ] MCP `prompts` entry: "Analyse a Google Sheet".
- [ ] Per-connector page on the site (install + example analyses).

### 1.6 Artifact storage (paid)  ⬜
- [ ] Migration `0002_artifacts.sql`: `results`, `run_metadata` (NEVER raw data) + Storage bucket.
- [ ] Server: `save_result` paid tool → signed-URL upload of the result artifact + metadata.
- [ ] Account page lists saved results.
- [ ] **✅ Phase 1 exit:** a stranger finds the page → subscribes → installs → connects a Sheet → gets an analysis → result saved.

---

## Phase 2 — Connector breadth
### 2.1 Shopify · 2.2 Stripe (ref `stripe-insights-mcp`) · 2.3 GA4 — BYO-creds + pages  ⬜
### 2.4 OAuth broker (Supabase Edge Functions) for Shopify + GA4 (one-click connect)  ⬜
- [ ] `oauth_tokens` table (encrypted) + per-provider redirect/exchange/refresh functions. Tokens brokered server-side; **data fetched machine→provider directly**.
### 2.5 SEO content engine  ⬜ — platform owner-story posts (use `website-article` skill) feeding both funnels.
- [ ] **✅ Phase 2 exit:** 3–4 real connectors, one-click OAuth on the top two.

## Phase 3 — Depth & scale
### 3.1 Connectors: Klaviyo · Meta Ads · Google Ads · WooCommerce · own-DB (Postgres/BigQuery)  ⬜
### 3.2 Pro/Team tier (seats, priority support) — held in reserve  ⬜
### 3.3 Usage analytics + polish  ⬜

---

## Tool split (done 2026-07-19)
Per locked decision (connectors + artifact storage are the ONLY paid features), **all 44 current
analytics/session tools are FREE**:

_Free (core, local — all existing):_ create_session, list_sessions, session_info, add_table,
scratchpad_add/read/search, relationships, join, run_sql, create_table, insert_into, count_rows,
count_non_null, profile, detect_outliers, analyze_association, association_matrix, combine_columns,
transform_column, bin_column, expand_datetime, group_aggregate, row_aggregate, normalize_fractions,
compute_feature, cluster, profile_clusters, reduce_dimensions, train_classifier, train_regressor,
evaluate, feature_importance, add_predictions, explain_prediction, decompose, forecast,
detect_changepoints, explain_metric, market_basket, causal_effect, rfm, retention_cohorts,
compare_periods.

_Paid (to be built):_ every `connectors/*` fetch tool + `save_result`/artifact tools.

_Optional future lever (NOT doing now):_ if the free tier proves too generous, the heavy tools
(forecast, causal_effect, train_classifier/regressor, retention_cohorts, market_basket) could move
behind paid. Recorded as a knob, not a decision — free-for-all-analytics stands.

## Cross-cutting guardrails
- Fast-by-default ML: LightGBM/RF default, no RBF-SVM default, bounded CV, feature/row guards.
- Determinism: fixed seeds everywhere (already core to `tabint`).
- Privacy invariant: only key/device/token/opt-in-artifact leaves the machine — assert this per connector.
- Idempotency: any server→control-plane write keyed to avoid double effects.

## Open confirmations (non-blocking)
- Post-trial: drop to free tier (recommended) vs hard lock. → **default: free tier.**
- Trial: card-up-front (better conversion) vs no-card (less friction). → decide at 0.5.
- App hosting: Astro SSR/Vercel routes in `shubham-site` vs separate `app.` deploy. → decide at 0.5/1.1.

---

## Progress Log
- 2026-07-19 — Plan created. Surveyed both repos (`tabint` FastMCP server + Astro site).
- 2026-07-19 — Step 0.3 (tool split) classification done: all 44 analytics tools free; paid = future connectors + artifacts.
- 2026-07-19 — **0.2 done**: `entitlement.py` (validate-key client, device id, fail-open, `requires_paid` decorator) + `account_status` tool; 10 tests passing; server imports clean.
- 2026-07-19 — **0.3 done**: gating mechanism in place (all tools free; paid decorator ready for connectors).
- 2026-07-19 — **0.1 partial**: branded console-script aliases + keywords added; PyPI-name change and Private-classifier removal deferred to the publish PR.
- 2026-07-19 — **0.4 scaffolded** (Supabase): core migration + `validate-key`. Then **pivoted the backend to Neon (DB) + Vercel functions** — Supabase hit the 2-active-free-project limit and Neon/Vercel is one platform. Migration ports over; edge function → Vercel function. Plans updated.
- 2026-07-19 — **Control plane rebuilt as a proper layered package** per Shubham's
  repository→service→endpoint + factory/facade rule. `control-plane/tabint_control/` (db facade +
  factory, 4 repositories, 2 services, CLI endpoint). **DuckDB local / Postgres-Neon prod**, chosen
  by env. Client `entitlement.py` wired to the service in local mode. **17 tests pass**; full flow
  demoed on DuckDB (mint→paid, device cap, free fallback). Old flat `_control_core.py` + raw SQL
  migration removed. `steps_for_shubham.md` created for deferred accounts/deploys.
- **Local dev needs no accounts.**
- 2026-07-19 — **Honesty seam (STEPWISE A1) — infra + exemplars done.** `src/tabint/honesty.py`
  (`Trust`/`TrustLevel` + assessors + `decline`); `Result.trust` field; `result_dict` emits a
  uniform `trust` + `declined` on every tool (default `unassessed`); MCP instructions updated.
  Retrofitted `compare_periods` (sample-size trust + not-causal caveat) and `causal_effect`
  (decline-to-answer on too-few-rows / no-variation / failed refutation; caps at moderate).
  `tests/test_honesty.py` + updated causal test; **200 tests pass**. Envelope verified in
  serialized output.
- 2026-07-19 — **Honesty seam A1 COMPLETE.** Swept all 13 analytics modules (5 parallel agents) —
  every one of the 44 tools now carries real trust + method-specific caveats, with decline-to-answer
  on unsupportable data (causal, forecast, models, market_basket, rfm/retention, association,
  cluster). Guarded `workspace`/`mcp_server._train` against declined-`Result`; fixed association
  constant-column (answer definitively, not decline) + bumped a persistence test's train fixture.
  **200 tests pass**; `trust` presence verified on every Result return.
- 2026-07-19 — **Stripe connector (B1) + normalization contract (A2) DONE.** `src/tabint/
  connectors/`: `contract.py` (canonical payments/customers/subscriptions/invoices + `conform`),
  `base.py` (registry + `Connector` ABC + `materialize`), `stripe.py` (urllib REST, pagination,
  cents→units, epoch→UTC). MCP: `connect_stripe` (paid, `requires_paid`, BYO key, data stays local),
  `list_connectors` (free), `stripe` prompt. E2E: connect→canonical tables→rfm/profile with honesty
  envelope. `tests/test_connectors_stripe.py` (7); **207 total pass**.
- 2026-07-19 — **ARCHITECTURE PIVOT + focus shift.** Connectors paused. New target = the full
  end-to-end loop. **MCP server holds NO user data** (analytics only; DuckDB just loads CSVs; calls
  website APIs). **All control plane / user mgmt / reports / payments / dashboard move INTO the
  Vercel website** (`shubham-site`, Astro+Vercel, TypeScript; DB facade DuckDB-local / Neon-prod;
  repo→service→endpoint in TS). **Payments = Razorpay.** Python `control-plane/tabint_control/` is
  now the schema/logic blueprint, not the deployed backend; `entitlement.py` → API-client-only.

  **Website build sequence (shubham-site, TS):**
  1. Astro SSR + Vercel adapter; layered backend skeleton (`src/server/db|repositories|services|
     endpoints`) with DB facade (DuckDB local / Neon prod).
  2. Auth: email+password signup/login (local), sessions; users table; **3-day trial** on signup.
  3. Razorpay: checkout + webhook → premium tier. (test keys → steps_for_shubham)
  4. Reports + folders: tables/repos/services; API endpoints the MCP calls (`/api/reports`,
     `/api/folders`) + dashboard pages (list folders/reports, view, share).
  5. MCP-facing API: `/api/validate-key` (entitlement), `/api/reports` (save/list/get). MCP
     `entitlement.py` + new report tools call these over HTTP.
  6. Marketing + docs + install-guide (Cowork/Claude Code/Codex/Cursor) pages.
  - Full loop: signup(trial) → pay(Razorpay) → install MCP → CSV+queries → generate+save report
    (MCP→website API) → login → dashboard folders/reports.
- 2026-07-19 — **END-TO-END LOOP BUILT & VERIFIED LOCALLY.** `shubham-site` = Astro SSR (Vercel
  adapter) + TS control plane (repo→service→endpoint, DB facade DuckDB-local/Neon-prod). Built:
  email/password auth (scrypt) + cookie sessions + 3-day trial + MCP key; reports/folders + services;
  APIs `/api/{auth/signup,auth/login,auth/logout,validate-key,account,billing/checkout,folders,
  reports,reports/:id,reports/:id/share}`; pages `/product`,`/pricing`,`/signup`,`/login`,`/dashboard`,
  `/dashboard/reports/:id`,`/r/:token`. Razorpay deferred (dev-grant premium). MCP side: `platform.py`
  + tools save/list/get report + create/list folder; `entitlement.py` → `<site>/api/validate-key`.
  VERIFIED via curl + Python: signup→trial→validate-key→rfm on CSV→save_report→dashboard→share→
  upgrade→paid. Build passes; 207 Python tests pass. Runbook: `shubham-site/RUNBOOK.md`.
  **Only account-gated bits remain (Razorpay/Neon/deploy) in `steps_for_shubham.md`.**
