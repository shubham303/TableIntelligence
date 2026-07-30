# Agents

How Table Intelligence is built to be used by an AI agent harness (Claude,
Codex, Cursor, …), and the design rules that keep it composable.

## The one idea

Table Intelligence is **one composable component** for an AI agent harness to
draw on — not the whole system. It does exactly one thing: **deterministic,
reproducible, local analysis of single-table data**. The harness pairs it with
whatever other tools the user has (GitHub, deploy, CMS, email, a browser, …) and
composes them at runtime.

```
                       ┌─────────────────────────────────────┐
   User query  ──────▶ │ Agent harness (Claude, Codex, …)    │
                       │  composes whatever tools fit        │
                       └───┬──────────────────────────────────┘
                           │
                  ┌────────▼──────────────┐
                  │ tabint (analysis MCP) │   + the harness wires in whatever
                  │  ~40 analytics tools  │     else the user has — these are
                  │  run LOCALLY (DuckDB) │     NOT ours and not assumed:
                  │  raw data never leaves│       GitHub · deploy · CMS · email …
                  └───────────────────────┘
```

The harness is given a **diverse but limited** set of tools (ours + the user's
other MCP servers/CLIs) and figures out, per query, **how to compose them** to
solve the problem. Table Intelligence never assumes which other tools exist.

## The governing principle: own the read, defer the write

Decide per capability whether it's a **read** or a **write**, then:

- **Own the reads.** The data that shapes every analysis here is **the user's
  own data**, read locally in-process via DuckDB. That is the load-bearing
  privacy property: raw tables never leave the user's machine. (Two small
  opt-in read clients reach out over HTTP only when explicitly wired — the
  Stripe connector to fetch a connected account's tables, and `entitlement` to
  look up a subscription tier; both fail safe / open if unset.)
- **Defer the writes to systems we don't own.** Raising/merging a PR,
  deploying, publishing to a CMS, sending email — these mutate external systems
  the user owns and picks the vendor for. Table Intelligence **does not wrap
  them, depend on them, or tie to their vendors.** It emits analysis results
  and lets the harness apply them with whatever the user has. This keeps the
  server vendor-neutral and avoids silently mutating systems outside the
  user's dashboard.

> The read/write line is a *deliberate* decision, documented so the harness
> knows what it can rely on.

## What this repo is, and what it is not

**Is** — a single MCP server (`tabint`) exposing one set of deterministic
data-science `@mcp.tool()` / `@mcp.prompt()` definitions, plus an opinionated
knowledge base (`study/`) the prompt refers to:

- `analysis` — descriptive → diagnostic → predictive → causal analytics, run
  locally on the user's machine via DuckDB.

**Is not** — a system that owns GitHub, a deploy platform, a CMS, an email
provider, or a browser. **Those write/exec tools belong to the harness.** We do
not wrap them, depend on them, or tie to their vendors.

This boundary is deliberate and load-bearing. A tool that bundles its own
GitHub/Vercel/CMS clients is a monolith the harness can't recompose and is
locked to those vendors; a tool that owns its reads and emits results is a
building block the harness pairs with *any* GitHub, *any* deploy platform,
*any* CMS the user has.

## Design rules

1. **One capability.** This server owns one domain: tabular data analysis. It
   exposes its tools and a prompt. It does one thing well.
2. **Depend only on `tabint.shared`.** The analysis package imports the shared
   `mcp` instance and shared helpers; it depends on no other feature package.
   (See `docs/architecture.md` for the one-way dependency rule:
   `app` → `shared` ← `analysis`.)
3. **Own the read, defer the write (per the principle above).** Run analysis on
   the user's local data in-process. Do NOT own write/exec on external systems
   (deploy, merge, send email, publish to a CMS) — emit results and let the
   harness execute them.
4. **Knowledge bases are first-class.** The `study/` folder is part of the
   server's value — it's the reference the prompt tells the LLM to read. Keep
   it opinionated, written-to-be-read, and self-contained.
5. **Honesty over reach.** State what this server does NOT do (send raw data
  off-machine; own GitHub/deploy/CMS/email). That boundary is what makes it
  safe to compose: the harness always knows which tool is responsible for each
  outward action.

## The analysis capability in this repo

| Capability | Package | Tools | Prompt | Knowledge base | Owns (reads) | Does NOT (writes/exec) |
|---|---|---|---|---|---|---|
| Data science | `tabint.analysis` | ~40 analytics `@mcp.tool()` | (inline `stripe` prompt) | `study/` | the user's local data (DuckDB) | send raw data off-machine |

It is registered onto the shared `FastMCP` by importing `analysis.tools` in
`src/tabint/app/mcp_server.py`.

## How a query flows (the harness's job, not ours)

For example, "analyse this CSV, then email the summary to my team": the harness
calls **Table Intelligence** (run the analysis locally, return structured
findings) → then its own **email tool** (send, after user approval). We did not
wire the email step. The harness did, by composing two independent tools. That
is the model.
