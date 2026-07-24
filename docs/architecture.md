# Architecture

## Two layers
1. **Deterministic core** — plain functions that compute. Directly callable by any
   user who knows what they want. This is the whole of V0 and most of the library.
2. **Orchestration (future)** — an agent that maps a natural-language question to a
   sequence of calls into the deterministic core. It has **no private
   capabilities**: anything it can do, a direct caller can do, because they're the
   same functions. The agent contributes planning and narration only — never
   computation.

This separation is what makes a future UI, API, or agent all thin clients over one
core.

## The four rigid contracts
Features can grow freely, but these four stay disciplined — they're the spine:

1. **Structured results.** Every analytics function returns a `Result` object with
   addressable fields (method chosen, statistic/values, metadata, optional
   artifact) and a readable `__repr__`. Never print-and-return-None. Two audiences
   read every result: a human (repr) and, later, the agent (fields).
2. **Centralized validation.** Column dtype classification and statistical
   assumption checks live in `analysis/service/validation/` and are reused
   everywhere. No function re-decides "is this column categorical?" — that's the
   main anti-duplication mechanism.
3. **Single table owner + write-back.** A `Workspace` owns one DuckDB connection
   holding one or more tables; each `Table` handle is the only place new columns
   are added for its table. ML results (cluster labels, predictions) are
   *materialized back as columns*, which turns follow-up questions about them into
   ordinary queries.
4. **Operation identity + caching.** Operations hash to a stable key so expensive
   work is never recomputed for the same inputs — essential once slow jobs exist.

## Two kinds of return
Most functions return an inert `Result` (data + repr). **`train_*` is the
exception**: it returns a `TrainedModel` — a live, *callable* artifact that bundles
its own fitted preprocessing (encoders, scaler, feature list) so new rows are
transformed identically at predict time (this prevents train/serve skew).
`predict` is a method on the model, not on the session. The session keeps a
registry of models (`s.models[name]`) so the agent can reference one by name, but
behavior lives on the model object.

## Fast lane vs slow lane
- **Fast lane** — descriptive stats, association tests, PCA, a single quick model,
  most clustering. Returns inline in seconds.
- **Slow lane** — AutoML (AutoGluon), exhaustive hyperparameter search, and a few
  O(n²) methods on large data. Runs as a **job** (id, status, result, error) in
  the background and writes results back as columns on completion. Querying the
  result afterward is fast again, because it's now just a column.

The split is driven by **estimated cost** (≈ rows × features × an algorithm
factor), not a static per-algorithm label — the same k-means is instant on 10k rows
and a job on 50M.

## Package layout (feature-oriented)
`src/tabint/` is organized into vertical slices. Each feature owns its endpoints
(MCP tools) and service logic; features depend only on `integration/` + `shared/`,
never on each other's internals. The composition root (`app/`) wires the features
onto a single FastMCP server and exposes the CLI.

```
src/tabint/
├── __init__.py            public API (Session, Result, Workspace, Table, …)
├── app/                   composition root — entry points
│   ├── mcp_server.py      slim registration root: imports feature tools modules, main()
│   └── cli.py             argparse CLI (JSON-per-command), delegates to the core
├── analysis/              FEATURE: data analysis
│   ├── tools.py           ~30 MCP tool defs (session lifecycle, structure, analytics)
│   ├── session.py         Session facade (thin state holder over a Workspace)
│   ├── service/
│   │   ├── workspace.py   Workspace + Table (the table owner / write-back surface)
│   │   ├── relationships.py   foreign-key detection (SQL inclusion dependencies)
│   │   ├── _prep.py       shared model-ready matrix builder
│   │   ├── algorithms/    the 14 analytics families (descriptive, association, …)
│   │   ├── validation/    dtype classification + assumption checks (routing input)
│   │   └── jobs/          slow-lane job model (registry + runner)
│   └── db/
│       ├── ducktable.py   DuckDB write mechanics (_ti_row id, ordered read/write)
│       └── persistence.py on-disk sessions (data.duckdb + models/ + meta.json)
├── outreach/              FEATURE: outreach agent
│   ├── tools.py           ~15 MCP tools (templates/campaigns/emails/reports CRUD)
│   └── prompts.py         the outreach-agent prompt (loaded once as a playbook)
├── integration/           ALL external API clients
│   ├── schemas/stripe.py  canonical Stripe table shapes (normalization contract)
│   └── service/
│       ├── base.py        Connector ABC + registry
│       ├── platform.py    control-plane client (reports + outreach), x-api-key
│       ├── entitlement.py key-validation client (free/pro, fail-open)
│       └── stripe.py      Stripe REST connector
└── shared/                generic cross-cutting code
    ├── results.py         the Result contract
    ├── honesty.py         Trust seam (confidence levels + decline-to-answer)
    ├── serialize.py       numpy/NaN-safe JSON (jsonable + result_dict)
    ├── identity.py        operation hashing + caching keys
    ├── scratchpad.py      per-session append-only notes
    └── server.py          the single FastMCP instance + live session registry
```

## Build order rationale
Foundation first (nothing works without it), then `analyze_association` as the first
real function — because its structured-return shape becomes the template every other
function copies, and it forces the dtype-driven method selection that is the
conceptual heart of the whole library. The agent is built *last*, by which point its
entire action space is already tested and trustworthy, shrinking its failure surface
to selection and argument-filling only.
