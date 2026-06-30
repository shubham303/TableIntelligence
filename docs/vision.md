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
