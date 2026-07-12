# 05 — Unsupervised learning (clustering & dimensionality reduction)

Code: `analytics/clustering.py` (`cluster`, `profile_clusters`) and
`analytics/dimreduction.py` (`reduce_dimensions`). Library: scikit-learn (UMAP optional).

"Unsupervised" = there is **no target column to predict**. You're asking the data to reveal
its own structure. Contrast with supervised learning (note 08), which needs a labelled Y.

## Part A — Clustering with k-means (`cluster`)
### Intuition
Given customers described by several numbers (spend, frequency, recency, age…), group them
so that members of a group are similar to each other and different from other groups —
*without* telling the algorithm what the groups are. It discovers segments RFM's fixed
rules can't.

### How it works
1. **Preprocess**: features are standard-scaled (mean 0, std 1) and categoricals one-hot
   encoded — essential, because k-means uses distances and an unscaled "revenue" in
   thousands would swamp an "age" in tens.
2. **k-means**: pick `k` cluster centres, assign each point to the nearest, move the centres
   to the mean of their points, repeat until stable.
3. **Choosing k automatically**: if you don't specify `k`, it tries k = 2…10 and picks the
   one with the best **silhouette score** — a −1…1 measure of how well-separated the
   clusters are (higher = cleaner separation). ~0.5+ is a genuinely good structure; near 0
   means the clusters overlap and may not be real.
Labels are written back as a `cluster` column, so "what's different about cluster 2?" is
just a query — answered by `profile_clusters`, which reports each cluster's size, numeric
means, and dominant categorical values.

### Pitfalls
- k-means assumes roughly round, similar-size clusters; it struggles with elongated or
  very uneven groups.
- A low silhouette means "don't oversell these segments" — they may be an artefact.
- Garbage-in: cluster on meaningful features, not IDs or written-back columns (the code
  excludes those on purpose).

## Part B — Dimensionality reduction (`reduce_dimensions`)
### Intuition
You can't eyeball 20 columns at once. Dimensionality reduction squeezes many features into
2–3 new ones that preserve as much structure as possible — mainly so you can **plot** the
data and *see* clusters, or feed a cleaner space back into clustering.

### The three methods
- **PCA** — linear; finds the directions of greatest variance. Fast, deterministic, and it
  reports **explained variance ratio** (how much information the 2 components keep). The
  honest default.
- **t-SNE** — non-linear; great at making visual clusters pop, but distances *between*
  clusters aren't meaningful and it's slow. Visualization only, never for downstream math.
- **UMAP** — non-linear, faster than t-SNE, preserves more global structure. Optional
  dependency.
Components are written back as `pca_0`, `pca_1`, … so plotting or re-clustering is a query.

### Pitfalls
- t-SNE/UMAP layouts are for the eye, not for measurement — never read a distance off them.
- PCA components are combinations of original features, so they're less directly
  interpretable; lean on explained-variance to know how much you kept.

## Marketing / e-commerce angle
- **Behavioural segmentation beyond RFM.** Cluster customers on {recency, frequency, AOV,
  category mix, discount sensitivity} to discover segments like "full-price loyalists" vs
  "discount-only one-timers" — each needs a different marketing motion.
- **Persona discovery** the client didn't know existed, then `profile_clusters` gives you
  the plain-English description of each to put in the report.
- Reduction is mostly an internal tool (make the clusters visible for the deliverable), but
  a 2-D "map of your customer base" is a striking slide.
- Caution to carry into the sale: learned clusters need a decent number of customers to be
  trustworthy — this is a retainer-tier/e-comm tool, not something to run on 200 orders.
