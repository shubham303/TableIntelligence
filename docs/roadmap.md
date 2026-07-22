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
- **Monetization** — keep the deterministic-correctness/reproducibility layer
  cleanly separable, since that's both the present differentiator and the most
  natural future paid surface. No action needed yet beyond keeping it liftable.

## Resolved decisions
- **License** — Apache-2.0. The distributed package (library, CLI, MCP server) is
  fully open; monetization lives in the hosted control plane (Pro role,
  connectors, reports), not the client.
- **Naming** — `tabint` (PyPI package + import name). Published on PyPI;
  installable via `uvx tabint-mcp` with no local env setup.
