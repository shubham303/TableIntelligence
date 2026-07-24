# Agents

How Table Intelligence is built to be used by an AI agent harness (Claude,
Codex, Cursor, …), and the design rules that keep it composable.

## The one idea

**Build small, independent agents — never coupled ones.** The harness gets each
agent as its own set of tools/skills and composes them at runtime based on the
user's query. Table Intelligence is **one component** of that larger system, not
the whole system.

Concretely: the `analysis` (data-science) agent, the `outreach` agent, and the
`seo_agent` are **fully independent**. They do not import each other, call each
other, or even know about each other. There is no orchestration layer inside
this repo that chains them. The *harness* is the orchestrator.

```
                       ┌─────────────────────────────────────┐
   User query  ──────▶ │ Agent harness (Claude, Codex, …)    │
                       │  composes whatever tools fit        │
                       └───┬──────────┬──────────┬───────────┘
                           │          │          │
                  ┌────────▼──┐ ┌─────▼─────┐ ┌──▼──────────────┐
                  │ tabint    │ │ tabint    │ │ tabint seo_agent│
                  │ analysis  │ │ outreach  │ │  SEO reasoning  │
                  │ (tools)   │ │ (tools+   │ │  + study/seo KB │
                  │           │ │  prompt)  │ │  + GSC/DataFor- │
                  │           │ │           │ │  SEO READ tools │
                  └───────────┘ └───────────┘ └─────────────────┘
                       independent — no cross-imports, no code coupling
                                        │
                  the harness ALSO wires in these WRITE/EXEC tools — NOT ours:
                    GitHub MCP/CLI · deploy (Vercel or other) · CMS · email · browser · …
```

The harness is given a **diverse but limited** set of tools (ours + the user's
other MCP servers/CLIs) and figures out, per query, **how to compose them** to
solve the problem. This is what lets one harness solve a wide range of problems
without each agent reimplementing the world.

## The governing principle: own the read, defer the write

Decide per capability whether it's a **read** or a **write**, then:

- **Own the reads your prompts are tuned to.** If a data source shapes your
  agent's strategies (e.g. DataForSEO + Google Search Console shape every SEO
  strategy in `study/seo/`), fetch it yourself with an API-key client so the
  tuning stays tight and predictable. A user-installed third-party MCP for the
  same source is fine too — but we ship our own client so the agent is
  self-contained by default.
- **Defer the writes to systems you don't own.** Raising/merging a PR,
  deploying, publishing to a CMS, sending email — these mutate external systems
  the user owns and picks the vendor for (Vercel vs another deploy platform;
  headless vs Git vs DB CMS; Resend vs Gmail vs SMTP). Emit the *spec*; let the
  harness apply it with whatever the user has. This keeps us vendor-neutral and
  avoids an agent silently mutating systems outside its dashboard.

> The read/write line is the architect's call per agent. The point is that it's
> a *deliberate* decision, not an accident — and it's documented in that agent's
> README so the harness knows what it can rely on.

## What this repo is, and what it is not

**Is** — a single MCP server (`tabint`) exposing several **independent** agents,
each a set of `@mcp.tool()` / `@mcp.prompt()` definitions plus, where useful, a
knowledge base (`study/...`) the prompt refers to:
- `analysis` — deterministic data-science tools (run locally on the user's
  machine via DuckDB; the core privacy property).
- `outreach` — templates → campaigns → prospect emails; stores to the dashboard
  via the platform API. Does NOT send email (the harness uses the user's own
  email tool).
- `seo_agent` — SEO reasoning + knowledge base (`study/seo/`) + its own
  DataForSEO/GSC **read** clients (planned). Does NOT raise PRs, deploy, or
  publish to a CMS — it emits specs the harness ships.
- `social` — social-content awareness: templates → campaigns → search specs +
  drafted posts/replies, across reddit/medium/linkedin/twitter/facebook. Does
  NOT scrape or post/publish/reply on any platform — it emits search specs the
  harness runs and drafts content the user/harness publishes.

**Is not** — a system that owns GitHub, a deploy platform, a CMS, an email
provider, or a browser. **Those write/exec tools belong to the harness.** We do
not wrap them, depend on them, or tie to their vendors. (Read APIs we depend on
for tuning — like GSC and DataForSEO for SEO — we *do* wrap; see above.)

This split is deliberate and load-bearing. An agent that bundles its own
GitHub/Vercel/CMS clients is a monolith the harness can't recompose and is
locked to those vendors; an agent that owns its reads and emits change specs is
a building block the harness pairs with *any* GitHub, *any* deploy platform,
*any* CMS the user has.

## Design rules (for adding a new agent)

1. **One capability per agent.** An agent owns one domain (analysis, outreach,
   SEO). It exposes its tools and a prompt. It does one thing well.
2. **No cross-agent coupling in code.** Agents do **not** import each other.
   The SEO agent does not call the outreach agent; the analysis engine is not
   imported by `seo_agent`. If two agents could help with one query, the
   **harness** calls each in turn — that's its job, not ours.
3. **Depend only on `tabint.shared`.** Each agent imports the shared `mcp`
   instance and any shared helpers; it depends on no other agent package. (See
   `docs/architecture.md` for the one-way dependency rule: `app` → `shared` ←
   features.)
4. **Own the read, defer the write (per the principle above).** Wrap the read
   APIs your prompts are tuned to. Do NOT own write/exec on external systems
   (deploy, merge, send email, publish to a CMS) — emit the spec and let the
   harness execute it. Document the split in the agent's README.
5. **Knowledge bases are first-class.** A `study/<domain>/` folder is part of an
   agent's value — it's the reference the prompt tells the LLM to read. Keep it
   opinionated, written-to-be-read, and self-contained (it must not assume
   another agent's tools are present).
6. **Honesty over reach.** Each agent states what it does NOT do (the outreach
   agent: "does not send email"; the SEO agent: "does not deploy/merge/publish/
   raise PRs"). These boundaries are what make agents safe to compose: the
   harness always knows which tool is responsible for each outward action.

## Why independence matters

A limited set of composable tools beats a few mega-agents:
- **Diversity of solvable problems.** The harness solves queries we never
  anticipated by recombining tools in ways we didn't code.
- **Swappability.** The user's GitHub tool, email tool, CMS, and deploy tool
  are their choice. We don't assume a specific one.
- **Independent evolution.** The outreach agent can change without touching SEO;
  a new external tool (e.g. a new CMS) needs no change here.
- **Smaller surface, clearer trust.** Each agent's boundary ("does not …") is
  auditable on its own; the harness enforces the composition.

## The agents in this repo

| Agent | Package | Tools | Prompt | Knowledge base | Owns (reads) | Does NOT (writes/exec) |
|---|---|---|---|---|---|---|
| Data science | `tabint.analysis` | ~40 analytics `@mcp.tool()` | (inline `stripe` prompt) | `study/data science/` | the user's local data (DuckDB) | send raw data off-machine |
| Outreach | `tabint.outreach` | 22 outreach `@mcp.tool()` | `outreach_agent` | (in prompt) | dashboard data (via platform API) | send email (harness's email tool does) |
| SEO | `tabint.seo_agent` | `seo_how_it_works` (scaffold) | `seo_agent` | `study/seo/` | DataForSEO + Google Search Console read clients (planned) | raise/merge PRs, deploy, publish to CMS — emits specs the harness ships |
| Social | `tabint.social` | 25 social `@mcp.tool()` | `social_agent` + 5 `social_platform_*` | `study/social/` | (none — reads deferred: emits search specs the harness runs) | post/publish/reply/scrape on any platform — drafts content + saves reply targets; the harness discovers & publishes |

Each is registered onto the shared `FastMCP` by importing its module in
`src/tabint/app/mcp_server.py`. No agent knows about the others.

## How a multi-agent query flows (the harness's job, not ours)

For example, "improve my site's SEO and draft outreach to earn links": the
harness calls the **SEO agent** (reason about gaps, emit the prioritised backlog
and link-target list) → then calls the **outreach agent** (turn the target list
into drafted prospect emails) → then its own **email tool** (send, after user
approval). We did not wire any of that. The harness did, by composing three
independent tools. That is the model.
