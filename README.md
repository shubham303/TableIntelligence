# TableIntelligence *

A deterministic, reproducible intelligence layer for **single-table** data.

`tabular` is a Python library of statistical and machine-learning operations for
one table at a time. Each operation is a plain, directly-callable function with a
**structured, inspectable result** — and (in the future) an optional agent that
orchestrates these same functions from a natural-language question.

The design goal that sets it apart: **the same question yields the same, correct
answer every time, with the method it chose made explicit.** Code-generation tools
that write fresh pandas on every run can't promise that; this library is built so
the computation is deterministic and the statistical method is selected by
transparent rules, not improvised.

> **Status: V0 — skeleton only.** The structure and docs exist; algorithms are
> being added one at a time. See the roadmap below for what's implemented.

## Install (development)

```bash
pip install -e .
```

## Intended usage

Single table — the flat convenience API:

```python
from tabular import Session

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

The core is exposed to external agents (Claude Code, Claude Cowork) through a
terminal **CLI** and an **MCP server**, both driven by a persistent *session key*:

```bash
pip install -e ".[mcp]"                 # library + `tabular` CLI + `tabular-mcp` server
claude mcp add tabular -- tabular-mcp   # register with Claude Code
```

```bash
tabular load orders.csv customers.csv   # -> {"session_key": "s_ab12", "tables": [...], "relationships": [...]}
tabular associate order_total tier --session s_ab12 --table orders
```

See [`docs/agent-integration.md`](docs/agent-integration.md) for the full tool list
and Claude Code / Cowork setup. This replaces the originally-planned bespoke agent
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

Not yet chosen — see `docs/roadmap.md`. Do not assume any license until one is added.
