# TableIntelligence *

A deterministic, reproducible intelligence layer for **single-table** data.

`tabint` is a Python library of statistical and machine-learning operations for
one table at a time. Each operation is a plain, directly-callable function with a
**structured, inspectable result** — plus an **MCP server** that exposes the same
deterministic functions to any MCP-capable agent (Claude Cowork, Codex, Cursor).

The design goal that sets it apart: **the same question yields the same, correct
answer every time, with the method it chose made explicit.** Code-generation tools
that write fresh pandas on every run can't promise that; this library is built so
the computation is deterministic and the statistical method is selected by
transparent rules, not improvised.

> **Status: working library + MCP server.** Phases 0–8 of the roadmap are
> implemented and tested (225 tests passing); see the roadmap below.

## Install

The package is on PyPI. Requires Python ≥ 3.10.

```bash
# MCP server — no install needed, runs isolated via uvx
uvx --from tabint tabint-mcp --help

# or install the CLI + MCP server into your environment
pip install tabint
```

Verify it landed:

```bash
tabint --help        # the CLI
tabint-mcp --help    # the MCP server (stdio transport)
```

> The package is named `tabint`; `tabint-mcp` is the server command inside it,
> so uvx/pipx need `--from tabint` to find the package. No `uvx`? Install it
> with `curl -LsSf https://astral.sh/uv/install.sh | sh`, or use
> `pipx run --from tabint tabint-mcp --help` instead.

## Intended usage

Single table — the flat convenience API:

```python
from tabint import Session

s = Session.load("customers.csv")
s.profile()                                   # describe every column
s.analyze_association("city", "spending")     # picks the right test by dtype
model = s.train_classifier(target="churn")    # returns a TrainedModel
model.predict(new_row)                        # predict lives on the model
```

Multiple related tables — one workspace, foreign keys detected automatically:

```python
s = Session.load(["orders.csv", "customers.csv", "products.csv"])

s.relationships()                             # infers the FK graph:
#   orders.customer_id → customers.customer_id (100%)
#   orders.product_id  → products.product_id  (100%)

enriched = s.join(["orders", "customers"])    # materializes a new joined table
enriched.analyze_association("order_total", "tier")   # analytics run on it

s.table("customers").cluster()                # per-table handle for any table
```

Every analytic operates on **one table** — either an uploaded table or one produced
by `join`. Joins are the only cross-table operation; they collapse related tables
into a single table the rest of the library can reason about.

## Use it from an AI agent (CLI + MCP)

The core is exposed to any MCP-capable agent through a terminal **CLI**
(`tabint`) and an **MCP server** (`tabint-mcp`), both driven by a persistent
*session key*. First do the install above, then register the server with your
agent.

### Environment variables

All agents need these in the server's `env`. Set them once and reuse the block
in every config below.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `TABINT_API_KEY` | **yes** | — | Your `ti_…` key from `https://shubhamrandive.com/dashboard/account`. Absent → free role (all analytics still work; persisting reports to the dashboard needs an account, enforced server-side). |
| `TABINT_CONTROL_PLANE_URL` | no | `https://shubhamrandive.com` | Base URL of the control plane (reports, folders, key validation). |
| `TABULAR_BASE` | no | current dir | Where on-disk sessions are stored (`<base>/.tableint/sessions/`). |

### Claude Code / Claude Cowork / Claude Desktop

Register the server (Claude Code CLI):

```bash
claude mcp add tabint \
  --env TABINT_API_KEY=ti_your_key_here \
  --env TABINT_CONTROL_PLANE_URL=https://shubhamrandive.com \
  -- uvx --from tabint tabint-mcp
```

…or paste the JSON block into the MCP config (Cowork / Desktop):

```json
{
  "mcpServers": {
    "tabint": {
      "command": "uvx",
      "args": ["--from", "tabint", "tabint-mcp"],
      "env": {
        "TABINT_API_KEY": "ti_your_key_here",
        "TABINT_CONTROL_PLANE_URL": "https://shubhamrandive.com"
      }
    }
  }
}
```

### OpenAI Codex (CLI)

Add to `~/.codex/config.toml` (Codex reads MCP servers from `[mcp_servers.*]`):

```toml
[mcp_servers.tabint]
command = "uvx"
args = ["--from", "tabint", "tabint-mcp"]
env = { TABINT_API_KEY = "ti_your_key_here", TABINT_CONTROL_PLANE_URL = "https://shubhamrandive.com" }
```

### Cursor

Add to `.cursor/mcp.json` in your project (or *Settings → MCP* for global):

```json
{
  "mcpServers": {
    "tabint": {
      "command": "uvx",
      "args": ["--from", "tabint", "tabint-mcp"],
      "env": {
        "TABINT_API_KEY": "ti_your_key_here",
        "TABINT_CONTROL_PLANE_URL": "https://shubhamrandive.com"
      }
    }
  }
}
```

### Verify it works

After registering the server in any agent, ask it to call the `account_status`
tool — it should return your role:

```text
> call account_status
{"role": "pro", "pro_features_unlocked": true, ...}   # or {"role": "free", ...} if no key set
```

Or from the CLI directly:

```bash
tabint load orders.csv customers.csv   # -> {"session_key": "s_ab12", "tables": [...], "relationships": [...]}
tabint associate order_total tier --session s_ab12 --table orders
```

See [`docs/agent-integration.md`](docs/agent-integration.md) for the full tool
list and troubleshooting. This replaces the originally-planned bespoke agent
harness: any MCP-capable agent orchestrates the same deterministic functions.

## Documentation

- [`docs/vision.md`](docs/vision.md) — what this is and why it exists
- [`docs/architecture.md`](docs/architecture.md) — the layered design and contracts
- [`docs/algorithms.md`](docs/algorithms.md) — the full algorithm taxonomy
- [`docs/roadmap.md`](docs/roadmap.md) — phased build plan
- [`docs/adding-an-algorithm.md`](docs/adding-an-algorithm.md) — the recipe for each new function
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Algorithm roadmap

Tick a box when a function is implemented, tested, and documented. This list is the
single source of truth for "what to build next" — pick an unchecked item, research
it, implement it against an existing library, add it to the test harness, then
check it here.

### Phase 0 — Foundation (build first; everything depends on it)
- [x] `store` — load a table, run SQL, write columns back (DuckDB)
- [x] `results.Result` — the structured return contract
- [x] `validation.dtypes` — column type classification (the routing input)
- [x] `validation.assumptions` — normality / equal-variance / sample-size checks
- [x] `identity` — operation identity + caching key
- [x] `Session` — state holder that delegates to the analytics layer
- [x] eval harness — fixture CSVs + known-correct answers

### Phase 1 — Descriptive
- [x] `profile` — per-column type, distribution, missingness, cardinality, range
- [x] `detect_outliers` — IQR and z-score flags
- [x] `association_matrix` — pairwise association with the right measure per dtype

### Phase 2 — Association / hypothesis testing  *(flagship — build carefully)*
- [x] `analyze_association` — dtype-routed test selection + effect size

### Phase 3 — Clustering
- [x] `cluster` — scale, fit, pick k (silhouette), write labels back as a column
- [x] `profile_clusters` — characterize each cluster in plain terms

### Phase 4 — Supervised learning
- [x] `train_classifier` — fast lane, single model, proper split (returns `TrainedModel`)
- [x] `train_regressor` — fast lane, single model, proper split
- [x] `backend="tabicl"` — opt-in TabICL v2 tabular foundation model (in-context
  learning, no per-task training; needs the `tabicl` extra). Default `backend="gbt"`.
- [x] `TrainedModel.predict` / `.predict_proba` — bundled preprocessing
- [x] `evaluate` — full metric set + confusion matrix
- [x] `add_predictions` — write a model's predictions back as a column
- [ ] slow lane: AutoGluon wrapper as a job *(infra ready via `jobs`; wrapper not yet written)*
- [x] `jobs` — Job registry + background runner

### Phase 5 — Model interpretation
- [x] `feature_importance` — gain-based / permutation importance
- [x] `explain_prediction` — per-row SHAP values

### Phase 6 — Dimensionality reduction
- [x] `reduce_dimensions` — PCA, UMAP/t-SNE *(PCA + t-SNE native; UMAP optional)*

### Phase 7 — Time series  *(optional; only if tables have a time axis)*
- [x] `decompose` — trend / seasonality / residual
- [x] `forecast` — ARIMA / Prophet *(ARIMA via statsmodels; Prophet optional)*
- [x] `detect_changepoints` — where a series shifts *(ruptures; `insights` extra)*

### Phase 8 — Insight-extraction primitives  *(the "so what / why / what to do" layer)*
- [x] `explain_metric` — ranked key drivers + segment rules *(shallow sklearn tree)*
- [x] `market_basket` — association-rule / cross-sell mining *(mlxtend; `insights` extra)*
- [x] `causal_effect` — backdoor effect estimate + refutation *(DoWhy; `insights` extra)*
- [x] `rfm` — Recency/Frequency/Monetary quintile segmentation *(pandas)*
- [x] `retention_cohorts` — monthly cohort retention matrix *(pandas)*
- [x] `compare_periods` — before/after shift with significance + effect size *(scipy)*

### Later — large-data + orchestration  *(beyond V0)*
- [ ] large-data strategies (sampling, out-of-core, approximate methods)
- [ ] natural-language `ask()` agent over the deterministic core

## Scope

Every analytic operates on **a single table**. Multiple related tables can be
loaded into one **workspace** (a shared DuckDB database); foreign keys are detected
automatically and a `join` collapses related tables into a single derived table
that the analytics then treat like any other. Reshaping beyond FK joins (pivots,
complex multi-way transforms) remains upstream of where these algorithms begin.

## License

Apache License 2.0 — see [`LICENSE`](LICENSE). The distributed package (library,
CLI, and MCP server) is fully open source. Monetization lives entirely in the
hosted platform (the Stripe connector, cloud reports, and the Pro role), not in
the client software.
