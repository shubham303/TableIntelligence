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
   assumption checks live in `validation/` and are reused everywhere. No function
   re-decides "is this column categorical?" — that's the main anti-duplication
   mechanism.
3. **Single table owner + write-back.** `store` owns the table and is the only
   place new columns are added. ML results (cluster labels, predictions) are
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
  O(n²) methods on large data. Runs as a **job** (id, status, result, error) in the
  background and writes results back as columns on completion. Querying the result
  afterward is fast again, because it's now just a column.

The split is driven by **estimated cost** (≈ rows × features × an algorithm
factor), not a static per-algorithm label — the same k-means is instant on 10k rows
and a job on 50M.

## Module map
```
store / loader            data substrate (DuckDB) + ingestion
results                   the Result contract
validation/dtypes         column classification (routing input)
validation/assumptions    normality / variance / sample-size checks
identity                  operation hashing + caching
session                   thin state holder + delegation
analytics/descriptive     profile, outliers, association matrix
analytics/association      analyze_association (flagship, dtype-routed)
analytics/clustering       cluster, profile_clusters
analytics/supervised       train_classifier/regressor, TrainedModel, evaluate
analytics/interpretation   feature_importance, explain_prediction
analytics/dimreduction     reduce_dimensions
analytics/timeseries       decompose, forecast (optional)
jobs/registry, jobs/runner slow-lane job model
```

## Build order rationale
Foundation first (nothing works without it), then `analyze_association` as the first
real function — because its structured-return shape becomes the template every other
function copies, and it forces the dtype-driven method selection that is the
conceptual heart of the whole library. The agent is built *last*, by which point its
entire action space is already tested and trustworthy, shrinking its failure surface
to selection and argument-filling only.
