# 02 — Association & hypothesis testing (the flagship)

Code: `analytics/association.py` — `analyze_association`. Library: scipy.stats.
This is the most important note in the folder. The engine's own docstring calls it the
"flagship function", because *choosing the right test from the data types* is the core
skill of applied statistics.

## Intuition
"Are these two things related?" is the most common analytical question. The catch: the
*correct* way to answer depends on what kind of columns you have (number vs category) and
whether the data meets certain assumptions. `analyze_association` encodes that decision
tree so the right test is always chosen automatically.

## The master decision tree
It looks at the dtype pair and routes:

**continuous × continuous** (two numbers, e.g. ad spend vs revenue)
- both roughly normal → **Pearson correlation** (measures *linear* relationship)
- otherwise → **Spearman correlation** (measures *monotonic* relationship, rank-based)
- output `r` ∈ [−1, 1]: sign = direction, magnitude = strength; `r²` = share of variance
  explained.

**categorical × continuous** (a group vs a number, e.g. channel vs order value)
- assumptions OK (normal + equal variance + enough samples):
  - 2 groups → **independent t-test**
  - 3+ groups → **one-way ANOVA**
- assumptions fail (the common real-world case):
  - 2 groups → **Mann-Whitney U**
  - 3+ groups → **Kruskal-Wallis**
- effect size: **eta²** (parametric) or **epsilon²** (non-parametric) = share of the
  number's variance explained by the grouping.

**categorical × categorical** (two categories, e.g. device vs converted?)
- expected cell counts OK → **Chi-square**
- 2×2 with small expected counts → **Fisher's exact**
- effect size: **Cramér's V** ∈ [0, 1].

## Two numbers you must never confuse
1. **p-value** — the probability of seeing a relationship this strong *if there were truly
   none*. Small p (< 0.05 by convention) = "unlikely to be luck" = **statistically
   significant**. It says nothing about how *big* the effect is.
2. **Effect size** (r, eta², Cramér's V, …) — *how strong* the relationship is. This is
   what actually matters for business.

The classic trap: with enough data, a trivially small effect becomes "significant"
(p < 0.05). A million-row table will call a meaningless 0.01 correlation significant.
**Always report the effect size, not just the p-value.** The engine returns both, plus a
plain-word strength label (negligible/weak/moderate/strong/very strong).

## Assumptions (why the tree has two branches)
- **Normality** — is the data bell-shaped? Checked per group (`assumptions.is_normal`).
  Real marketing data (revenue, sessions) is skewed, so the **non-parametric branch
  (Mann-Whitney/Kruskal/Spearman) is what you'll use most.** That's a feature, not a
  fallback — non-parametric tests don't assume a distribution.
- **Equal variance** — do the groups have similar spread? (`has_equal_variance`.)
- **Enough samples** — small groups make parametric tests unreliable.
The chosen test and every assumption check land in the `Result.metadata` — your audit trail.

## Pitfalls
- **Correlation ≠ causation.** This entire family measures association only. "Ice-cream
  sales correlate with drownings" (both caused by summer). To make a causal claim you need
  note 10. Overclaiming here is the fastest way to lose a technical client's trust.
- **Confounding** — a hidden third variable driving both. Association can't see it.
- **Linear vs monotonic** — Pearson misses a strong curved relationship; Spearman catches
  monotonic ones. Neither catches a U-shape.

## Marketing / e-commerce angle
- "Does **email open rate** differ by **send time** (morning/afternoon/evening)?" →
  categorical × continuous → Kruskal-Wallis + epsilon² → a defensible send-time finding.
- "Is **discount depth** related to **order value**?" → continuous × continuous → Spearman.
- "Is **device** (mobile/desktop) associated with **converting**?" → categorical ×
  categorical → Chi-square + Cramér's V.
In every case you hand the client the strength *and* the significance, and you can name the
exact test — which is what separates you from a dashboard that just draws a trendline.
