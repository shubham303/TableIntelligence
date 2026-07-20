# Table Intelligence — Product Plan

_**Table Intelligence** — the TableIntelligence analytics core productized as an installable,
local-first MCP server, sold self-serve alongside the consulting service. Built by a solo dev;
deliberately low-overhead. Living document — last updated 2026-07-19._

## 1. Thesis & principles (the non-negotiables)

- **One MCP server, runs locally on any machine.** All compute (deterministic stats + ML)
  happens on the user's hardware. We ship no compute infra.
- **Their LLM, their CPU, our thin backend.** The user brings their own agent/LLM subscription
  and their own machine. Our hosted side does only: auth, subscription/payments, optional
  result+metadata storage, and OAuth token-brokering for connectors.
- **Privacy is the wedge.** Raw client data never leaves the machine. Only tokens/metadata/
  chosen result-artifacts ever touch our server. This is the sharpest differentiator vs
  server-side competitors (e.g. mcpanalytics.ai).
- **Pricing: flat $5/mo unlimited. Locked — not raising it.** Solo dev, low cost base, low
  income needs; simplicity beats squeezing. Marginal cost per run ≈ 0, so we don't meter.
  Guard key-sharing with a **2-device cap**.
- **Freemium + 3-day trial.** Free tier = core local analytics forever (the acquisition +
  privacy hook). New users get a **3-day trial** of the paid features; after that, $5/mo to
  keep them. **Paid-only features: connectors and cloud artifact storage.**
- **Single server, many connectors + platform prompts.** Never fork the server per platform.
  Core analytics tools are always present; connectors and platform-specific prompts plug in.
- **Distribution, not code, is the moat.** The code is a commodity; anti-piracy stays minimal.
  The win is packaging, docs, SEO, brand, and the connector breadth.

---

## 2. Target architecture

```
┌─────────────────────────── USER'S MACHINE ───────────────────────────┐
│  Agent host (Claude Desktop / Claude Code / Cowork / Codex / Cursor…) │
│        │  MCP (stdio)                                                 │
│        ▼                                                              │
│  data-analytics-mcp  (single Python server)                          │
│   ├── Core analytics tools  (always on)                              │
│   │     profile, group_aggregate, run_sql, rfm, forecast,            │
│   │     causal_effect, train_classifier, retention_cohorts, …        │
│   ├── Connector modules  (enabled per entitlement/config)            │
│   │     shopify, etsy, stripe, ga4, google_sheets, klaviyo, …        │
│   ├── Platform prompts   (MCP "prompts": how to analyse each source) │
│   └── Auth/entitlement client  (validates key, refreshes on schedule)│
│        Raw data pulled provider→machine, analysed locally. Stays here.│
└───────────────────────────────┬──────────────────────────────────────┘
                                 │  HTTPS: only tokens / metadata / opt-in artifacts
                                 ▼
┌───────────────────── CONTROL PLANE (Supabase + Stripe) ──────────────┐
│  Auth (API keys, device binding) · Subscriptions (Stripe webhooks)   │
│  OAuth broker (holds provider client secrets, token exchange+refresh)│
│  Optional store: result artifacts + run metadata (NEVER raw data)    │
└──────────────────────────────────────────────────────────────────────┘

           shubhamrandive.com (Astro static)      app.shubhamrandive.com (dynamic)
           marketing · docs · connector pages  →  signup · Stripe checkout · key mgmt
```

**Single-server / multi-connector design (point 5):**
- Core tools registered at startup, always available.
- Each connector is a **module** that registers its own data-fetch tools (e.g.
  `shopify.fetch_orders`) + a **platform prompt** (e.g. "analysing a Shopify store: pull
  orders, compute RFM/AOV/repeat-rate, watch for…"). Connectors are enabled by user config +
  entitlement, so the tool surface adapts per user without shipping a different binary.
- Platform prompts use the **MCP `prompts` primitive** so the host can offer "Analyse my
  Shopify data" as a ready workflow.

---

## 3. Workstreams (mapped to the 6 requests)

### WS1 — The MCP server (point 1)
- Package the existing `tabular` analytics core as `data-analytics-mcp` (Python).
- **Distribution:** publish to PyPI; run via `uvx data-analytics-mcp` (zero-clone install).
  Also ship a one-click **`.mcpb` bundle** for Claude Desktop.
- **Startup auth:** read API key from MCP config env var → validate against Supabase →
  cache entitlement, re-check on a schedule (flat pricing = no per-run check needed).
- **Fast-by-default guardrails** (baked in): default to LightGBM/XGBoost/RF, never RBF-SVM
  by default; bound hyperparameter search (small grid, ≤5-fold CV); guard feature explosion
  and huge inputs (downsample + warn). Keeps every run laptop-fast.
- Deterministic outputs (fixed seeds) so results are reproducible/citable.

### WS2 — Website install page + multi-platform guides (point 2)
- New page on shubhamrandive.com: **"Data Analytics MCP Server"** (Astro).
- **Working install guides**, one section per host, each verified end-to-end:
  - **Claude Desktop** — one-click `.mcpb`, plus manual `claude_desktop_config.json` snippet.
  - **Claude Code** — `claude mcp add` command.
  - **Claude Cowork** — connector/MCP add flow.
  - **Codex (OpenAI)** — `config.toml` MCP entry.
  - **Cursor / Windsurf / VS Code / Cline** — `mcp.json` / settings snippet.
  - Generic **stdio MCP** JSON for anything else.
  - _(Verify exact syntax per client at build time — MCP config formats drift.)_
- Each guide: prerequisites (Python/uv), the config block, where to paste the API key, a
  "verify it works" first-command, and troubleshooting.

### WS3 — Documentation (point 3)
- Docs site (Astro content collection or a `/docs` section):
  - **What it is / why local-first** (privacy, reproducibility, defensibility).
  - **Architecture** (the diagram above, data-flow, what leaves the machine).
  - **Tool reference** — every core tool: inputs, outputs, method chosen, assumptions.
  - **Quickstart** — from install → first analysis in 5 minutes.
  - **Recipes** — worked analyses (RFM, forecast, churn classifier, cohort retention).
  - **Data handling & privacy** — explicit statement of what is/ isn't sent to our server.
  - **Limits** — row/size guidance, what needs a connector.

### WS4 — Connectors + per-connector pages (point 4)
- A reusable **connector framework** (fetch client + OAuth hook + platform prompt), so a new
  connector is "a new API client," not new architecture.
- **Per-connector page on shubhamrandive.com** (also doubles as SEO):
  - What data the platform holds and what you can learn from it.
  - How to connect (BYO-credentials v1 → one-click OAuth later).
  - Example analyses specific to that platform.
- Auth pattern: **tokens brokered via our server, data fetched machine→provider directly**
  (raw data never transits our backend).
- **Connector roadmap (priority order):**
  1. Google Sheets · Shopify · Stripe · GA4  _(the universal four)_
  2. Klaviyo · Meta Ads · Google Ads  _(best-converting segments: e-comm retention, agencies)_
  3. WooCommerce · QuickBooks/Xero · Postgres/MySQL/BigQuery _(own-DB unlock for SaaS)_
  4. Etsy · Recharge · Google Search Console
  5. Vertical bundle — nonprofit CRMs (Donorbox/Bloomerang/Neon) **or** fitness (Mindbody)
     once that segment shows traction.
  - _Hard/deferred:_ Amazon SP-API, dental/vet PMS, Blackbaud, MLS.

### WS5 — Single-server discipline (point 5)
- Covered in §2. Enforce: no per-platform binaries; connectors + prompts are modules gated by
  config/entitlement; one versioned release of `data-analytics-mcp`.

### WS6 — Supabase + payments backend (point 6)
- **Supabase** (existing account) as the control plane. Core tables:
  - `users`, `api_keys` (hashed, device-bound), `subscriptions` (Stripe status),
    `devices` (for soft key-share cap), `oauth_tokens` (encrypted, per provider/user),
    `results` + `run_metadata` (opt-in artifact store — never raw data).
  - **RLS** on everything; tokens encrypted at rest.
- **Payments:** Stripe Checkout ($5/mo) + Billing Portal; **Stripe webhooks → Supabase Edge
  Function** to sync subscription state.
- **Auth/entitlement endpoint:** lightweight Edge Function the MCP calls to validate key +
  device + active subscription.
- **OAuth broker:** Edge Functions per provider for the redirect/exchange/refresh (holds
  client secrets). Hands tokens to the local MCP; never sees provider data.
- **app.shubhamrandive.com:** signup, checkout hand-off, "get your key," device management.

---

## 4. Phased roadmap

**Phase 0 — Foundations (make one thing work end-to-end)**
- Package `tabular` core → `data-analytics-mcp` on PyPI (`uvx` runnable).
- Supabase: users + api_keys + subscriptions; Stripe test-mode checkout; validate-key Edge fn.
- MCP validates key on startup against Supabase.
- Install working on **Claude Desktop + Claude Code** only.
- ✅ Exit: a paying test user installs, key validates, runs a local analysis.

**Phase 1 — Launchable product**
- Website product page + docs (WS2/WS3) for Claude Desktop, Claude Code, Codex, Cursor.
- `.mcpb` one-click bundle. Device cap. Stripe live. Billing portal.
- First connector: **Google Sheets** (BYO-credentials) end-to-end + its page.
- ✅ Exit: a stranger can find the page, subscribe, install, connect a Sheet, get an analysis.

**Phase 2 — Connector breadth**
- Shopify, Stripe, GA4 (BYO-creds) + per-connector pages.
- OAuth broker (one-click connect) for Shopify + GA4.
- SEO content engine spun up (platform owner-story posts feeding both funnels).
- ✅ Exit: 3–4 real connectors, one-click OAuth on the top two.

**Phase 3 — Monetization depth & scale**
- Klaviyo, Meta Ads, Google Ads, WooCommerce, own-DB connectors.
- Pro/Team tier (connectors/seats/support). Result-artifact store (opt-in). Analytics on usage.
- ✅ Exit: up-market tier live; connector library covers the top segments.

---

## 5. Tech stack
- **MCP server:** Python (existing analytics core), MCP SDK, packaged on PyPI + `.mcpb`.
- **ML/stats:** scikit-learn, LightGBM/XGBoost, statsmodels/Prophet, existing `tabular` libs.
- **Website/docs:** Astro (static) on the existing `shubham-site` repo.
- **App/backend:** **Neon (Postgres) + Vercel serverless functions** (validate-key, Stripe
  webhook, checkout, issue-key, OAuth) + Stripe. _(Switched from Supabase 2026-07-19 — Neon has
  no active-project cap and keeps everything in the existing Vercel account.)_ Artifact storage →
  Vercel Blob.
- **Secrets:** provider OAuth client secrets in Supabase; user tokens encrypted at rest;
  local tokens in OS keychain.

---

## 6. Decisions locked (2026-07-19)
1. **Python only** — no R in the runtime. Simplifies packaging/install (`uvx`).
2. **Freemium + 3-day trial.** Free core-analytics tier forever; 3-day trial of paid features;
   then $5/mo. _(Confirm the exact free-tier boundary — see below.)_
3. **Price: $5/mo, locked.** Not raising to $9–12; simplicity + low needs win.
4. **Artifact storage: paid-only** (also the retention hook for subscribers).
5. **Connectors: paid-only** (the headline reason to upgrade).
6. **Device cap: 2 devices** per key.
7. **Name: Table Intelligence.** PyPI package e.g. `table-intelligence` / `table-intelligence-mcp`.

### Monetization & gating
| Tier | Access |
|------|--------|
| **Free (forever)** | Core local analytics tools on local files (CSV/Excel/Sheets-paste). No connectors, no cloud artifact storage. Max 2 devices. |
| **3-day trial** | Everything paid, no card required up front (or card-on-file, TBD). |
| **Paid $5/mo** | Everything free + **connectors** + **cloud artifact storage** + 2 devices. |

**One boundary to confirm:** after the trial lapses without paying, does the user keep the
**free core-analytics tier** (recommended — keeps the funnel warm and the privacy hook alive),
or lose all access? Recommendation: drop to the free tier, not a hard lockout.

## 7. Top risks
- **Install friction** (Python deps across OSes) — mitigate with `uvx` + `.mcpb` bundle; test
  on clean machines.
- **Distribution** is the real bottleneck, not the build — needs the SEO/registry/content
  engine from Phase 2, budget real effort here.
- **MCP client config drift** — install snippets must be re-verified per release.
- **Key-sharing** on flat unlimited — device cap is the one control that matters.
- **Focus split** vs the service business — service stays the cash engine; product is a thin,
  opinionated slice pulled forward by real users.
```
