# Table Intelligence

Table Intelligence is a **deterministic, reproducible intelligence layer for single-table
data**, delivered as a single MCP server (package `tabint`) that plugs into Claude and other
AI agents. It runs locally on the user's machine via DuckDB — that is the core privacy
property: **the user's raw data never leaves their machine.**

## Architecture — the MCP server

This repo is the MCP server (`package `tabint`, src layout). It exposes **prompts,
resources, and tools** for one capability: **local tabular data analysis** (descriptive →
diagnostic → predictive → causal). There is no account data, no dashboard, and no
multi-agent orchestration here — it is one analysis server.

```
User's machine
┌───────────────────────────────────────────┐
│ AI agent (Claude, Codex, …)               │
│  └─ MCP server (tabint)                   │
│      └─ analysis tools run LOCALLY (DuckDB)│
│  raw data stays here ─────────────────────┘
└───────────────────────────────────────────┘
```

### What it does NOT do

- It does not send the user's raw data off-machine.
- It does not own or talk to the user's other systems (GitHub, deploy, CMS, email).
  Those write/exec tools belong to the host AI harness, not to `tabint`.

### The optional platform coupling (entitlement + Stripe)

Two small integrations reach out over HTTP, both **opt-in and informational**:

- **`entitlement`** (`tabint.integration.service.entitlement`) — looks up the user's
  subscription tier (`free`/`pro`) against a Table Intelligence web platform via
  `POST /api/validate-key`, authenticated with the user's `TABINT_API_KEY` in the
  `x-api-key` header. Feeds the informational `account_status` tool. The MCP server itself
  is free to use and imposes no client-side gating; the tier is reported, never enforced
  locally.
- **Stripe connector** (`tabint.integration.service.stripe`) — used by the
  `connect_stripe` / `list_connectors` tools and the `stripe()` prompt to fetch and
  materialize a connected Stripe account's canonical tables (locally, via DuckDB) for
  analysis.

The web platform that backs `entitlement` lives in a sibling repo (`shubham-site`,
Astro/Vercel + Neon Postgres). It is **not** required to run the MCP server — if
`TABINT_API_KEY` is unset, entitlement simply fails open to `free`.

## Conventions

- The MCP is **local-first**: never send the user's raw dataset anywhere; the analysis
  runs in-process on DuckDB.
- Analytics tools are free; there is no client-side gating. The Pro tier (if a platform is
  connected) is enforced server-side on the platform API, not here.
- The `entitlement` module is informational only — it feeds `account_status`.

## Repos

- **`TableIntelligence`** (this repo) — the MCP server. Python package `tabint` (src
  layout). The analytics engine (`analysis/`) + the small `integration/` package
  (entitlement + the Stripe connector).
- **`shubham-site`** (sibling, `../shubham-site`) — the web platform, when one is
  connected: Astro SSR on Vercel, Neon Postgres via `DATABASE_URL`. See
  `shubham-site/NEON.md` for its database setup.
