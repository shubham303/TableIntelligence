# tabular  *(placeholder name — rename before public release)*

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

## Intended usage (API preview — not yet implemented)

```python
from tabular import Session

s = Session.load("customers.csv")
s.profile()                                   # describe every column
s.analyze_association("city", "spending")     # picks the right test by dtype
model = s.train_classifier(target="churn")    # returns a TrainedModel
model.predict(new_row)                        # predict lives on the model
```

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
- [ ] `store` — load a table, run SQL, write columns back (DuckDB)
- [ ] `results.Result` — the structured return contract
- [ ] `validation.dtypes` — column type classification (the routing input)
- [ ] `validation.assumptions` — normality / equal-variance / sample-size checks
- [ ] `identity` — operation identity + caching key
- [ ] `Session` — state holder that delegates to the analytics layer
- [ ] eval harness — fixture CSVs + known-correct answers

### Phase 1 — Descriptive
- [ ] `profile` — per-column type, distribution, missingness, cardinality, range
- [ ] `detect_outliers` — IQR and z-score flags
- [ ] `association_matrix` — pairwise association with the right measure per dtype

### Phase 2 — Association / hypothesis testing  *(flagship — build carefully)*
- [ ] `analyze_association` — dtype-routed test selection + effect size

### Phase 3 — Clustering
- [ ] `cluster` — scale, fit, pick k (silhouette), write labels back as a column
- [ ] `profile_clusters` — characterize each cluster in plain terms

### Phase 4 — Supervised learning
- [ ] `train_classifier` — fast lane, single model, proper split (returns `TrainedModel`)
- [ ] `train_regressor` — fast lane, single model, proper split
- [ ] `TrainedModel.predict` / `.predict_proba` — bundled preprocessing
- [ ] `evaluate` — full metric set + confusion matrix
- [ ] `add_predictions` — write a model's predictions back as a column
- [ ] slow lane: AutoGluon wrapper as a job
- [ ] `jobs` — Job registry + background runner

### Phase 5 — Model interpretation
- [ ] `feature_importance` — gain-based / permutation importance
- [ ] `explain_prediction` — per-row SHAP values

### Phase 6 — Dimensionality reduction
- [ ] `reduce_dimensions` — PCA, UMAP/t-SNE

### Phase 7 — Time series  *(optional; only if tables have a time axis)*
- [ ] `decompose` — trend / seasonality / residual
- [ ] `forecast` — ARIMA / Prophet

### Later — large-data + orchestration  *(beyond V0)*
- [ ] large-data strategies (sampling, out-of-core, approximate methods)
- [ ] natural-language `ask()` agent over the deterministic core

## Scope

This library operates on **a single, already-prepared table**. Producing that
table (joins across multiple tables, reshaping) is intentionally out of scope and
lives upstream of where these algorithms begin. Every function assumes the table
it's handed is already the right shape.

## License

Not yet chosen — see `docs/roadmap.md`. Do not assume any license until one is added.
