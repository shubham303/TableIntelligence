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
