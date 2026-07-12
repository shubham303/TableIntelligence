# Integrating a Tabular Foundation Model into TableIntelligence

**Status:** Research + decision plan · **Date:** 2026-07-10
**Author:** research pass for Shubham
**Scope:** Should `tabular` add a tabular *foundation model* (TFM) as a prediction
backend, and if so, which one — and how does it fit our data-science-as-a-service model?

---

## 1. What these models actually are (the thing you half-remembered)

You were thinking of **TabPFN** ("Tabular Prior-data Fitted Network"). The category is
**tabular foundation models (TFMs)**: transformers pre-trained *once* on millions of
synthetic tables, that then do **in-context learning (ICL)** — you hand the model your
whole training table *at inference time* as context, and it predicts new rows **without
any gradient training on your data**. No `fit()` in the classical sense, no
hyperparameter tuning, no per-task weights.

Mechanically:
- Classical ML (our current `HistGradientBoosting`): `fit()` learns weights from *your*
  data → then `predict()`.
- TFM: weights are frozen from pre-training. `fit()` just *memorizes your table as
  context*; `predict()` runs one forward pass that attends over your training rows +
  the new row. The "learning" happened once, at the vendor, on synthetic data.

**Why anyone cares:** on small/medium tables they beat tuned XGBoost out of the box, in
seconds, with zero tuning. That is a real, measured result — not hype.

---

## 2. The landscape (2025–2026)

| Model | Task | Size ceiling | Speed | Open source? | Commercial use? |
|---|---|---|---|---|---|
| **TabPFN v2** | clf + reg | ~10k rows, 500 feat, 10 classes | GPU-fast | weights open | **non-commercial only** |
| **TabPFN 2.5** | clf + reg | ~50k rows, 2k feat | GPU-fast; distillation to MLP/trees for low latency | weights open | **non-commercial only** (Prior Labs sells enterprise license) |
| **TabPFN-3** | clf + reg | up to 1M×200, 100k×2k, or 1k×20k | GPU | weights open | **permissive for internal eval/benchmark; production needs paid license** |
| **TabICL / TabICL v2** | clf (v2 adds reg) | ~500k rows | ~10× faster than TabPFN v2 | **fully open (incl. commercial)** | ✅ |
| **TabDPT** | clf | medium | GPU | open | ✅ |
| **TabFlex** | clf | millions (linear attention) | fast | open | ✅ |
| **CARTE** (INRIA) | clf + reg, cross-table transfer | medium | GPU | open | ✅ |
| **LimiX / Mitra / ContextTab / Orion-*** | clf | varies | varies | mostly open | mixed |

Sources at the bottom. Two families matter for us:
1. **TabPFN family** — best accuracy, #1 on the TabArena benchmark, **but the good
   checkpoints are non-commercial-licensed.**
2. **TabICL family** — nearly-as-good, ~10× faster, **fully open including commercial.**

---

## 3. The two things that decide this for *us specifically*

### 3.1 The licensing trap (this is the deciding factor)

Our V1 pivot is **a services company** — we run analyses for paying clients (see
`memory/v1-pivot-services-via-agents.md`). That makes model licensing a hard gate, not
a footnote:

- **TabPFN v2 / 2.5 weights are non-commercial.** Using them to produce a deliverable
  a client pays for is exactly the prohibited use. Prior Labs sells a commercial
  enterprise license (managed API / VPC / on-prem) if we want them.
- **TabPFN-3** is explicitly permissive for internal evaluation and benchmarking but
  **production still needs the paid license.**
- **TabICL is fully open including commercial use.** No gate.

> **Implication:** if we integrate a TFM to *ship client results*, the default pick is
> **TabICL v2**, not TabPFN — unless we're willing to pay Prior Labs. TabPFN is fine for
> *internal* R&D, benchmarking, and "is a TFM even worth it here" experiments.

### 3.2 Fit with data-science-as-a-service

Our pitch is **data science as a service** — we deliver analyses/models to paying
clients. A TFM helps or hurts that in concrete ways:

- ✅ **Good:** on small/medium tables a TFM beats tuned trees out of the box in seconds,
  with zero tuning — that's faster, better client deliverables for less analyst time,
  which is exactly the leverage a service business wants.
- ✅ **Good:** inference is a single forward pass with frozen weights → same input gives
  the same output, so results are reproducible across client runs.
- ⚠️ **Watch:** it's a **black box** — feature importance is post-hoc (permutation only)
  and per-prediction "why" is limited. If a client needs an explainable model, a TFM may
  not be the right deliverable.
- ⚠️ **Operational:** GPU strongly recommended (CPU only viable for ≲1000 rows). That's a
  real dependency/infra change for a library that today is pure-Python + sklearn with
  "no fragile system deps."

> **Implication:** a TFM should be an **opt-in "power" backend** we reach for when it
> produces a better client deliverable — a labeled, explicitly-selected alternative, not
> the silent default.

---

## 4. Where it plugs in (the code is already shaped for this)

Good news: the codebase anticipated this. `src/tabular/analytics/supervised.py:8-10`
literally says HistGradientBoosting *"is a drop-in swap point for xgboost / lightgbm /
autogluon (the slow lane) later."* A TFM is exactly that swap.

- **Integration point:** `supervised.py` → `train_classifier` / `train_regressor`.
- **Surface:** add a `backend=` param, e.g.
  `s.train_classifier(target="churn", backend="tabicl")` (default stays `"gbt"`).
- **Contract:** the TFM estimator has a sklearn-style `.fit()/.predict()/.predict_proba()`,
  so it slots behind the existing `TrainedModel` wrapper (`supervised.py:44`) with
  **no change** to `session.py`, `workspace.py`, `cli.py`, or `mcp_server.py` — they all
  delegate through the same `TrainedModel`. Preprocessing pipeline (`_prep.py`) mostly
  still applies (impute/encode), though TFMs prefer raw-ish numeric + light encoding.
- **Guardrails to add:** row/feature-count check → refuse or fall back to GBT when the
  table exceeds the model's ceiling; a clear `method`/`backend` field in the `Result`
  so it's recorded which backend produced the deliverable; a "no-GPU → CPU only if
  small" check.

Rough effort: **~1–2 days** for a gated TabICL backend behind `backend=`, plus tests,
because the wrapper and delegation layers already exist.

---

## 5. Recommendation — what to integrate, what to skip

| Model | Verdict | Why |
|---|---|---|
| **TabICL v2** | ✅ **Integrate first** | Fully open **incl. commercial**, ~10× faster, handles ~500k rows, now does regression. The only one that clears our services-licensing gate cleanly. |
| **TabPFN 2.5** | 🟡 **Internal/benchmark only** | Best accuracy + #1 TabArena, but **non-commercial weights**. Use it as our *quality ceiling* to measure TabICL against, and to decide whether Prior Labs' paid license is worth it. Do **not** ship client work on it unlicensed. |
| **TabPFN-3** | 🟡 **Watch / eval** | More permissive for internal eval; production still paid. Re-evaluate if we ever buy a Prior Labs license. |
| **CARTE** | 🟡 **Later, niche** | Its edge is *cross-table* transfer — interesting once we lean into the multi-table/FK story, not now. |
| **TabFlex / TabDPT / LimiX / Mitra / Orion-*** | ⛔ **Skip for now** | Redundant with TabICL for our needs; more moving parts, less proven, some licensing unclear. Revisit only if a specific dataset breaks TabICL. |

**Bottom line:** integrate **TabICL v2** as an opt-in `backend="tabicl"` power-lane;
use **TabPFN 2.5** internally as a benchmark yardstick only; skip the rest until a
concrete need appears.

---

## 6. Open questions before we build

1. **Do we actually have small-data clients?** TFMs win biggest on *small/medium* tables.
   If our client tables are routinely >500k rows, tuned GBT/AutoGluon may still win and
   the TFM is a distraction. → Sanity-check against real `datasets/`.
2. **GPU infra.** Are we willing to add a GPU path (or a hosted-inference dependency)? If
   deployment must stay CPU-only, TFMs are limited to tiny tables — big constraint.
3. **Explainability bar.** Is a black-box backend acceptable as a client deliverable, or
   do some engagements require an explainable model? Decide per-engagement.
4. **Benchmark first.** Before writing the integration, run a 1-afternoon spike: TabICL
   vs TabPFN 2.5 vs our current GBT on 3–4 real client-like tables. Only integrate if
   the accuracy delta is real on *our* data.

---

## 7. Proposed next step

Run the **§6.4 benchmark spike** (throwaway script, GPU box or Colab) before any library
change. If TabICL beats our GBT meaningfully on real tables → implement the gated
`backend="tabicl"` per §4. If not → document the finding and skip; we keep the simpler
sklearn stack.

---

## Sources
- [The state of Tabular Foundation Models (2026) — Christoph Molnar](https://mindfulmodeler.substack.com/p/the-state-of-tabular-foundation-models)
- [TabPFN-2.5: Advancing the State of the Art (arXiv 2511.08667)](https://arxiv.org/abs/2511.08667)
- [PriorLabs/TabPFN GitHub + LICENSE](https://github.com/PriorLabs/TabPFN)
- [Prior Labs docs — quickstart / licensing](https://docs.priorlabs.ai/quickstart)
- [TabPFN — Wikipedia](https://en.wikipedia.org/wiki/TabPFN)
- [Tabular Models Benchmark across 19 datasets (AIMultiple, 2026)](https://aimultiple.com/tabular-models)
- [What Foundation Models Exist for Structured Enterprise Data? (Kumo.ai, 2026)](https://kumo.ai/resources/learn/comparison/foundation-models-structured-enterprise-data/)
