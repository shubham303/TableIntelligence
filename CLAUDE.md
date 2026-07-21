# Table Intelligence

Table Intelligence is a **suite of AI agents** (data analysis, outreach, and more) delivered as a
single MCP server that plugs into Claude and other AI agents, backed by a web platform for
accounts, billing, and a dashboard.

## Architecture — two parts

The project has **two parts** that live in two repos:

1. **The MCP server** (this repo, `TableIntelligence`) — a local Python MCP server (package
   `tabint`). It only exposes **prompts, resources, and tools**. It holds no user account data of
   its own; for anything that needs to be stored, it **calls the web platform's HTTP APIs** to do
   CRUD on that data.

2. **The web platform + APIs** (sibling repo `shubham-site`, Astro on Vercel + Supabase Postgres) —
   user accounts, auth, subscriptions/billing, the dashboard, and the **REST APIs** the MCP server
   calls. It stores only **dashboard-relevant data and the output of the various agents** (e.g.
   saved analysis reports; outreach templates, campaigns, prospects, drafted emails, received
   emails).

### How they fit together

- **Data-analysis tools live in the MCP server and run locally on the user's machine** (via DuckDB
  / the `tabint` engine). This is the core privacy property: **the user's raw data never leaves
  their machine.** Only the outputs the user chooses to save (e.g. a report, an outreach draft) are
  sent to the platform.
- **The MCP server calls the platform APIs** (authenticated with the user's API key,
  `TABINT_API_KEY`) to create/read/update/delete that dashboard data.
- **The web frontend calls the same APIs** (authenticated by the login session) to display and edit
  that data. So both the MCP server and the dashboard read/write the same records through one API
  layer.

```
User's machine                              Cloud (shubham-site)
┌───────────────────────────┐               ┌──────────────────────────────┐
│ AI agent (Claude, …)      │   HTTP APIs   │ Web platform (Astro/Vercel)  │
│  └─ MCP server (tabint)   │──────────────▶│  ├─ REST APIs (/api/*)       │
│      ├─ analysis tools    │  (API key)    │  ├─ Dashboard (session)      │
│      │   run LOCALLY      │               │  └─ Supabase Postgres        │
│      └─ calls APIs to     │◀──────────────│      (accounts + agent       │
│         store outputs     │   data        │       outputs only)          │
│  raw data stays here ─────┘               └──────────────────────────────┘
```

## Repos

- **`TableIntelligence`** (this repo) — the MCP server. Python package `tabint` (src layout). The
  analytics engine + the outreach connector tools. The MCP holds no DB; `src/tabint/platform.py` is
  its HTTP client to the platform APIs.
- **`shubham-site`** (sibling, `../shubham-site`) — the web platform: Astro SSR on Vercel, Supabase
  Postgres via `DATABASE_URL`, `src/server/{db,repositories,services,lib}` + `src/pages/api/*` +
  the `/dashboard` UI. See `shubham-site/SUPABASE.md` for the database setup.

## Conventions

- The MCP is **local-first**: never send the user's raw dataset to the platform; only send outputs
  the user explicitly saves.
- All persisted data goes through the platform APIs — the MCP server never talks to a database
  directly.
- Analytics tools are free; connectors (outreach, etc.) and cloud storage are the paid tier, gated
  server-side on the API by subscription and mirrored client-side by `entitlement.requires_paid`.
