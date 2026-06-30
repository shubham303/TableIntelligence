# Claude Code prompt — scaffold the repository for a tabular-data intelligence library (V0)

Paste everything below this line into Claude Code.

---

You are setting up a brand-new Python library repository. Your job in this session
is **structure and documentation only**. Do **NOT** implement any algorithm,
statistical method, or ML logic. Every function and method you create is a
skeleton that raises `NotImplementedError` (or contains `...`) with a clear
docstring. The point is a clean, installable, well-documented skeleton that I will
fill in one algorithm at a time over the coming months.

Read these constraints carefully and follow them exactly:

- **No algorithm implementations.** Foundation plumbing (loading data, running SQL,
  writing columns back) is also left as skeleton for now — V0 is purely the shape.
- The package must be **pip-installable** (`pip install -e .`) and **importable**
  without errors. A smoke test should confirm `import` works and that calling an
  unimplemented method raises `NotImplementedError`.
- Keep dependencies **minimal and declared but mostly unused for now**: `duckdb`,
  `pandas`, `numpy` as runtime deps; `pytest` as a dev dep. Do not add scikit-learn,
  scipy, statsmodels, xgboost, autogluon, etc. yet — list them in docs as
  *planned* per-family dependencies, not installed now.
- Do **not** set up CI, publishing, release automation, or versioning workflows.
  No GitHub Actions. I'll handle releases much later.
- Use a **`src/` layout**. Use `pyproject.toml` (hatchling or setuptools backend —
  your choice, keep it simple).
- The distribution/import name `tabular` is a **PLACEHOLDER**. Add a prominent note
  in the README that I should rename it before any public release.
- Write all the docs and the README using the exact content I provide below.
  Where I provide full content, reproduce it faithfully. Where I describe a
  skeleton, write idiomatic minimal Python.

## Directory structure to create

```
.
├── README.md
├── pyproject.toml
├── LICENSE                      # placeholder: see note below
├── .gitignore
├── CONTRIBUTING.md
├── docs/
│   ├── vision.md
│   ├── architecture.md
│   ├── algorithms.md
│   ├── roadmap.md
│   └── adding-an-algorithm.md
├── src/
│   └── tabular/
│       ├── __init__.py
│       ├── session.py
│       ├── results.py
│       ├── store.py
│       ├── loader.py
│       ├── identity.py
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── dtypes.py
│       │   └── assumptions.py
│       ├── analytics/
│       │   ├── __init__.py
│       │   ├── descriptive.py
│       │   ├── association.py
│       │   ├── clustering.py
│       │   ├── supervised.py
│       │   ├── interpretation.py
│       │   ├── dimreduction.py
│       │   └── timeseries.py
│       └── jobs/
│           ├── __init__.py
│           ├── registry.py
│           └── runner.py
└── tests/
    ├── __init__.py
    ├── fixtures/
    │   └── .gitkeep
    └── test_smoke.py
```

## Code skeleton specifications

All skeletons should have type hints and docstrings. Methods/functions bodies
should `raise NotImplementedError("planned: see docs/roadmap.md")` unless noted.

### `src/tabular/__init__.py`
Export the public surface. For V0 that's just `Session` and the base `Result`
type. Include a module docstring naming the library and pointing to `docs/`.

```python
"""tabular — a deterministic, reproducible intelligence layer for single-table data.

Public API is intentionally small. See docs/architecture.md for the design and
docs/roadmap.md for what's implemented vs. planned.
"""
from tabular.session import Session
from tabular.results import Result

__all__ = ["Session", "Result"]
__version__ = "0.0.0"
```

### `src/tabular/results.py`
Define the structured-return contract. A `Result` dataclass is the base type that
every analytics function returns. Include fields for the chosen method, the primary
statistic/values, metadata, and an optional raw artifact, plus a readable
`__repr__`. Add a short docstring noting that `TrainedModel` (in `supervised.py`)
is a *separate* callable type, not a `Result` — it bundles fitted preprocessing and
exposes `.predict()`.

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Result:
    """Base structured return for every analytics function.

    Two audiences read this: a human at a REPL (via __repr__) and, later, an
    orchestrating agent (via addressable fields). Keep fields explicit.
    """
    method: str                       # what was actually run/chosen
    summary: str = ""                 # one-line plain-language summary
    values: dict[str, Any] = field(default_factory=dict)  # statistics, scores, etc.
    metadata: dict[str, Any] = field(default_factory=dict)  # assumptions, params used
    artifact: Any = None              # optional raw object (model, fitted transform)

    def __repr__(self) -> str:        # readable for humans
        return f"<Result method={self.method!r} summary={self.summary!r}>"
```

### `src/tabular/session.py`
A thin state holder. Holds the store, a dict of trained models, and (later) a job
registry. Each public method delegates to the analytics layer — but in V0 every
method raises `NotImplementedError`. Include `load` as a classmethod. Methods to
stub: `load`, `profile`, `detect_outliers`, `analyze_association`,
`association_matrix`, `cluster`, `profile_clusters`, `train_classifier`,
`train_regressor`, `evaluate`, `feature_importance`, `reduce_dimensions`,
`add_predictions`, `run_sql`. Add a docstring on the class explaining it is
deliberately thin: state + delegation only. Note in a comment that `predict` lives
on the returned `TrainedModel`, **not** on `Session`.

### `src/tabular/store.py`
Skeleton for the DuckDB-backed table store. Stub methods: `load_csv(path)`,
`run_sql(query)`, `write_back_column(name, values)`. Docstring explains this is the
single owner of the table and the only place columns are added (the
"materialize-as-column" mechanism).

### `src/tabular/loader.py`
Skeleton for CSV/dataframe ingestion + initial dtype inference on load. Stub
`load(path)`.

### `src/tabular/identity.py`
Skeleton for operation identity / caching. Stub `operation_key(name, params,
column_fingerprint)` returning a stable hash string. Docstring explains it exists
so expensive operations (slow-lane jobs) are never recomputed for the same inputs.

### `src/tabular/validation/dtypes.py`
Skeleton for column classification. Stub `classify_column(series)` →
returns one of {"continuous", "categorical_nominal", "categorical_ordinal",
"datetime", "identifier"}; and `classify_table(df)` → mapping. Docstring stresses
this is the single source of truth reused by every analytics function (the main
anti-duplication mechanism).

### `src/tabular/validation/assumptions.py`
Skeleton for statistical assumption checks. Stub `is_normal(series)`,
`has_equal_variance(*groups)`, `enough_samples(...)`, `expected_counts_ok(table)`.
Docstring explains these *route* test selection in the association family.

### `src/tabular/analytics/*.py`
One module per family. Each module gets a docstring naming the family, the planned
functions, and the external library it will eventually use (listed as a comment,
not imported). Provide stub function signatures that raise `NotImplementedError`:

- `descriptive.py` → `profile`, `detect_outliers`, `association_matrix`. Lib: pandas/numpy.
- `association.py` → `analyze_association`. Lib: scipy.stats, statsmodels.
  Add a thorough docstring here describing the dtype-routing logic (continuous×continuous → Pearson/Spearman; categorical×continuous → t-test/ANOVA/Kruskal + effect size; categorical×categorical → chi-square/Fisher + Cramér's V), since this is the flagship and template function.
- `clustering.py` → `cluster`, `profile_clusters`. Lib: scikit-learn.
- `supervised.py` → `train_classifier`, `train_regressor`, `evaluate`, plus a
  `TrainedModel` class skeleton (a callable artifact with `.predict()` and
  `.predict_proba()` stubs that bundles preprocessing). Lib: scikit-learn,
  xgboost/lightgbm.
- `interpretation.py` → `feature_importance`, `explain_prediction`. Lib: shap.
- `dimreduction.py` → `reduce_dimensions`. Lib: scikit-learn, umap-learn.
- `timeseries.py` → `decompose`, `forecast`. Lib: statsmodels, prophet. Mark optional.

### `src/tabular/jobs/registry.py` and `runner.py`
Skeletons for the slow-lane job model. `registry.py`: a `Job` dataclass (id,
status in {"running","done","failed"}, result, error) and an in-memory registry
stub. `runner.py`: a `run_async(...)` stub. Docstring explains the fast-lane /
slow-lane split: quick ops return inline; genuinely slow ops (AutoGluon, big
tables) run as jobs and write results back as columns on completion.

### `tests/test_smoke.py`
A minimal test that (1) imports `tabular`, (2) constructs nothing that needs data
but asserts `Session` exists and is importable, and (3) asserts that calling an
unimplemented method raises `NotImplementedError`. This proves the skeleton is
wired correctly without implementing anything.

### `pyproject.toml`
Configure: project name `tabular` (note placeholder), version `0.0.0`,
description, Python `>=3.10`, runtime deps `duckdb, pandas, numpy`, optional dev
group with `pytest`, src layout package discovery. No entry points, no plugins.

### `.gitignore`
Standard Python ignore (`__pycache__/`, `*.egg-info/`, `.venv/`, `dist/`,
`build/`, `.pytest_cache/`, `.DS_Store`).

### `LICENSE`
Create a placeholder file containing a single line:
`TODO: choose a license before any public release (see docs/roadmap.md).`
Do not pick a license for me.

---

## Now create the documentation files with this exact content.

### === FILE: README.md ===

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

### === END FILE ===

### === FILE: docs/vision.md ===

# Vision

## What this is
A Python library that brings statistical and machine-learning analysis to **single
tables**, where each capability is a plain, directly-callable function returning a
**structured, inspectable result**. A future layer adds an agent that answers
natural-language questions by orchestrating these same functions — but the
functions are the foundation and come first.

## Why it exists
Two kinds of tool already exist and each is incomplete:
- **Natural-language-to-dataframe tools** generate code on the fly. They're
  flexible but **non-reproducible** (the same question can yield different code and
  different answers on reruns) and offer **no statistical-correctness guarantees**.
- **AutoML tools** model without manual tuning, but have **no natural-language
  layer** and assume you already know exactly what to model.

The empty seam between them is **reliable, reproducible, correct analysis driven by
intent**. That seam is the reason this library exists.

## The core principle
**Computation is deterministic; method selection is rule-based and transparent.**
A given operation on given data produces the same result every time, and the chosen
method (which test, which model, which assumptions) is always reported. When the
agent layer arrives, it only ever *selects and narrates* — it never originates a
number. Every statistic comes from a real, tested library (scipy, scikit-learn,
statsmodels, etc.), never from a language model.

## What "good" looks like
The single most convincing demonstration: ask the same analytical question twice
and get the **same correct answer**, with the method shown — next to a code-gen
tool that gives two different answers. That contrast is the whole reason-to-exist
in one screenshot.

## Scope discipline
Single table only. The algorithms assume a prepared table. Multi-table preparation
(joins, reshaping) is out of scope and, if ever added, slots in *upstream* without
touching the algorithms. This boundary keeps the focus on algorithmic depth rather
than relational plumbing.

## Posture
Built primarily as a deep, hands-on exploration of the tabular ML/stats space —
implemented one algorithm at a time, each understood properly before it's added.
Open-source first. Monetization, licensing, and any hosted version are deliberately
deferred; the priority is a correct, coherent library.

### === END FILE ===

### === FILE: docs/architecture.md ===

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

### === END FILE ===

### === FILE: docs/algorithms.md ===

# Algorithm taxonomy

The master list of capability families. The README checklist mirrors this; this
file carries the detail. Grow the library along these families rather than by
accretion — every new function should belong to one of them and declare its
**precondition** (what it assumes about the data).

## 1. Descriptive / exploratory
Column profiling (type, distribution, missingness, cardinality, range, sample
values), outlier detection (IQR, z-score), and pairwise association. Foundation for
everything and the context a future agent reads to understand a table. *Libraries:
pandas, numpy.*

## 2. Association / hypothesis testing
"Is there a relationship between A and B," routed entirely by the dtype pair:
- continuous × continuous → Pearson (normal) / Spearman (otherwise)
- categorical × continuous → t-test / one-way ANOVA (assumptions hold) /
  Mann-Whitney / Kruskal-Wallis (otherwise), **plus** an effect size (eta² / ε²)
- categorical × categorical → chi-square (cell counts allow) / Fisher, plus Cramér's V

The *selection logic* is the lesson here, not the computation. *Libraries:
scipy.stats, statsmodels.*

## 3. Clustering
k-means, hierarchical, DBSCAN, Gaussian mixtures. Requires feature scaling first;
k chosen via silhouette/elbow rather than blindly. Labels written back as a column;
each cluster profiled into plain-language character. *Library: scikit-learn.*

## 4. Dimensionality reduction
PCA (linear, interpretable), t-SNE / UMAP (visualization). Pairs with clustering.
*Libraries: scikit-learn, umap-learn.*

## 5. Supervised learning
Classification and regression. Default to **gradient-boosted trees** — on tabular
data they're the workhorse and usually beat deep learning. Proper train/test
splitting, categorical encoding, missing-value handling. Fast lane = one quick
model; slow lane = AutoML. *Libraries: scikit-learn, xgboost, lightgbm; autogluon
(slow lane).*

## 6. Model interpretation
Feature importance (gain-based, permutation) and per-prediction explanations
(SHAP). Answers "why" once you can predict. *Library: shap.*

## 7. Time series *(optional)*
Decomposition (trend/seasonality/residual), autocorrelation, forecasting
(ARIMA, Prophet). A somewhat separate world; build only if tables carry a time
axis. *Libraries: statsmodels, prophet.*

## Beyond the families (later)
- **Large-data strategies** — sampling, out-of-core computation, approximate
  algorithms for when a table doesn't fit in memory. This is where algorithm
  knowledge turns into systems thinking.
- **Recommendation systems** — collaborative filtering, matrix factorization.
  Note: these need a user-item interaction table, which usually implies a join,
  so they sit at the edge of the single-table scope and belong to the far-future
  multi-table vision.

### === END FILE ===

### === FILE: docs/roadmap.md ===

# Roadmap

A phased plan. Each phase makes the next more useful. Within a phase, implement one
function at a time using the recipe in `adding-an-algorithm.md`, and check it off in
the README.

## Phase 0 — Foundation
The deterministic spine: `store` (load/SQL/write-back), `Result`, `validation`
(dtypes + assumptions), `identity`, `Session`, and the eval harness. No analytics
yet. Nothing above works until this is solid.

## Phase 1 — Descriptive
`profile`, `detect_outliers`, `association_matrix`. Doubles as the context a future
agent will read.

## Phase 2 — Association *(flagship)*
`analyze_association`. The first function that forces dtype-driven method selection.
Its result shape becomes the template for everything after. Get the
categorical-vs-continuous case right (ANOVA/Kruskal, not Pearson).

## Phase 3 — Clustering
`cluster` + `profile_clusters`. Builds the write-back-as-column machinery in earnest.

## Phase 4 — Supervised
Fast-lane `train_classifier` / `train_regressor` → `TrainedModel.predict` →
`evaluate` → `add_predictions`. Then the `jobs` model and the AutoGluon slow lane.

## Phase 5 — Interpretation
`feature_importance`, `explain_prediction`.

## Phase 6 — Dimensionality reduction
`reduce_dimensions`.

## Phase 7 — Time series *(optional)*
`decompose`, `forecast`.

## Later (beyond V0)
- Large-data strategies (sampling, out-of-core, approximate methods).
- The natural-language `ask()` agent over the deterministic core.
- (Far future, out of current scope) multi-table prep enabling the
  database-to-recommendations vision.

## Deferred decisions (revisit deliberately, not now)
- **License** — pick before any public release. Permissive (MIT/Apache) maximizes
  adoption and embedding; consider a separate license for any future hosted piece.
- **Monetization** — keep the deterministic-correctness/reproducibility layer
  cleanly separable, since that's both the present differentiator and the most
  natural future paid surface. No action needed yet beyond keeping it liftable.
- **Naming** — `tabular` is a placeholder; choose and rename before publishing.

### === END FILE ===

### === FILE: docs/adding-an-algorithm.md ===

# Adding an algorithm — the repeatable recipe

Follow these steps for every new function so the library stays coherent as it grows.

1. **Pick** the next unchecked item from the README roadmap.
2. **Research** it properly — understand the method, its assumptions, and when it's
   the *wrong* choice. Don't implement what you can't yet explain.
3. **Write the precondition** first: what must be true of the input data (dtypes,
   no missing values, minimum sample size, scaling). Encode it using the shared
   `validation/` helpers — do not re-implement dtype or assumption checks locally.
4. **Implement** using an existing, trusted library (scipy / scikit-learn /
   statsmodels / xgboost / etc.). The library does the math; your code does
   selection, validation, and packaging. Never compute statistics by hand.
5. **Return a `Result`** (or, for `train_*`, a `TrainedModel`). Populate `method`,
   `summary`, `values`, `metadata` (include the assumption-check outcomes that drove
   any choice). Keep `__repr__` readable.
6. **Materialize** any new data back as a column via `store.write_back_column`
   (e.g. cluster labels, predictions) so follow-ups become ordinary queries.
7. **Test** against the eval harness: add a fixture case with a known-correct answer.
   For deterministic methods, correctness is largely checkable — keep these strict.
8. **Document** the function and **check the box** in the README.

## Invariants to never break
- Structured returns, never print-and-return-None.
- Reuse `validation/`; never duplicate dtype/assumption logic.
- `store` is the only writer of columns.
- The method chosen and its assumptions are always reported in the result.
- Computation is deterministic; the same inputs give the same outputs.

### === END FILE ===

### === FILE: CONTRIBUTING.md ===

# Contributing

This project is built one algorithm at a time. Before adding anything, read
`docs/vision.md` and `docs/architecture.md` — they define the contracts every
contribution must honor.

## To add a capability
Follow `docs/adding-an-algorithm.md` exactly. In short: pick an unchecked roadmap
item, research it, write its precondition with the shared `validation/` helpers,
implement it against an existing library, return a structured `Result`, add a
known-answer test to the harness, document it, and check the box in the README.

## Non-negotiable invariants
- Structured, inspectable returns (never print-and-return-None).
- Centralized dtype/assumption checks — no local duplication.
- `store` is the single owner and writer of the table.
- Deterministic computation; transparent, rule-based method selection.
- Computation comes from trusted libraries, never improvised.

## Setup
```bash
pip install -e ".[dev]"
pytest
```

### === END FILE ===

---

## Final steps for you, Claude Code

1. Create every file and directory above.
2. Run `pip install -e .` and then `pytest` to confirm the package installs,
   imports cleanly, and the smoke test passes (calling an unimplemented method
   raises `NotImplementedError`).
3. Initialize a git repository and make a single initial commit
   (`chore: scaffold V0 structure and docs`). Do not configure remotes, CI, or
   releases.
4. Print a short summary of what you created and confirm the smoke test passed.

Remember: **no algorithm implementations in this session.** Structure and docs only.