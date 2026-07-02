# Books to Read

Organised by what you need them for. Free PDF links included where available.

---

## Foundation — Statistics & Method Selection

**Practical Statistics for Data Scientists** — Bruce, Bruce & Gedeck
The most directly useful book for this project. Covers exactly the decisions
`analyze_association` needs to make: when to use Pearson vs Spearman, t-test vs
Mann-Whitney, chi-square vs Fisher. Written for people who code, not statisticians.
- Free PDF: https://github.com/gedeck/practical-statistics-for-data-scientists

**Statistics in Plain English** — Timothy Urdan
Short, clear explanations of every test in the library: t-tests, ANOVA,
Kruskal-Wallis, chi-square, correlation. Best book for understanding *when* a test
applies and what it assumes.
- Buy: widely available, cheap

**OpenIntro Statistics** — Diez, Çetinkaya-Rundel & Barr
Full undergraduate statistics textbook. Covers hypothesis testing, effect sizes,
regression, and assumptions. Rigorous but readable.
- Free PDF: https://www.openintro.org/book/os/

---

## Effect Size — The Part Most Tools Skip

**Statistical Power Analysis for the Behavioral Sciences** — Jacob Cohen
The canonical reference for effect sizes (Cohen's d, r, f). You only need the
first chapter — 20 pages — to understand what d, r, and f mean and when each
applies. Everything else in the book is lookup tables.
- Free PDF: https://www.utstat.toronto.edu/~brunner/oldclass/378f16/readings/CohenPower.pdf

---

## Machine Learning & Supervised Methods

**An Introduction to Statistical Learning (ISLR)** — James, Witten, Hastie & Tibshirani
The standard reference for `train_classifier`, `train_regressor`, `evaluate`.
Covers train/test splits, cross-validation, overfitting, ROC curves, and feature
importance properly. Python edition available.
- Free PDF: https://www.statlearning.com

**The Elements of Statistical Learning (ESL)** — Hastie, Tibshirani & Friedman
The deeper, more mathematical version of ISLR. Reference level — use it to
understand *why* an algorithm works, not how to call it.
- Free PDF: https://hastie.su.domains/ElemStatLearn/

---

## Clustering

**Introduction to Data Mining** — Tan, Steinbach & Kumar
Best practical coverage of clustering: k-means, silhouette score, choosing k,
and cluster evaluation. Chapters 7-8 are directly applicable to `cluster` and
`profile_clusters`.
- Free PDF: https://www-users.cse.umn.edu/~kumar001/dmbook/index.php

---

## Causal Thinking — The Part That Makes Answers Trustworthy

**Causal Inference: The Mixtape** — Scott Cunningham
Understanding confounders, Simpson's paradox, and why a correlation isn't an
answer. Essential for building an agent that doesn't mislead users.
- Free: https://mixtape.scunning.com

**The Book of Why** — Judea Pearl & Dana Mackenzie
Accessible introduction to causal reasoning. Less technical than Mixtape but
builds the right intuition for what questions data can and cannot answer.
- Not free, but widely available in libraries

---

## Time Series (Phase 7)

**Forecasting: Principles and Practice** — Hyndman & Athanasopoulos
The standard reference for `decompose` and `forecast`. Covers ARIMA, seasonal
decomposition, Prophet-style models, and evaluation metrics for time series.
- Free: https://otexts.com/fpp3/

---

## Build Order Recommendation

1. *Practical Statistics for Data Scientists* — read before implementing `analyze_association`
2. *OpenIntro Statistics* Ch 5-7 — hypothesis testing foundations
3. *Cohen Ch 1* — effect sizes, before any p-value reporting
4. *ISLR* — before implementing `train_classifier` / `train_regressor`
5. *Causal Inference: The Mixtape* Ch 1-2 — before building the agent skills layer
6. *Clustering chapter from Introduction to Data Mining* — before `cluster`
7. *Forecasting: Principles and Practice* — only if you build Phase 7
