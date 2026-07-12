# 01 — Descriptive statistics (the foundation)

Code: `analytics/descriptive.py` — `profile`, `detect_outliers`, `association_matrix`.
Libraries: pandas, numpy, scipy.stats.

## Intuition
Before any modelling, you look at the data: what type is each column, how much is missing,
what's the range, is anything obviously broken. Every serious analysis starts here, and
half of all "insights" are really just good descriptive work presented well.

## The concepts

### Column profiling (`profile`)
For each column it reports **type, missingness, cardinality (n_unique), and a distribution
summary**. For a numeric ("continuous") column: min, max, mean, median, std, and **skew**.
For a categorical column: the top-5 most frequent values and their counts.

- **Mean vs median.** Mean is the average; median is the middle value. When they diverge,
  the data is skewed (a few big values pulling the mean). For money columns (order value,
  revenue) the median is usually the honest "typical" number.
- **Standard deviation (std)** — how spread out the values are. Small std = values cluster
  near the mean; large std = they're all over the place.
- **Skew** — asymmetry. Right/positive skew (long tail of large values) is the norm for
  revenue, order value, session duration. It matters because it breaks the "normal
  distribution" assumption that many tests rely on (see note 02).
- **Cardinality** — number of distinct values. High cardinality on an ID-like column tells
  you it's an identifier, not a feature; low cardinality flags a category.

### Outlier detection (`detect_outliers`) — two methods, union of both
1. **IQR method.** Q1 and Q3 are the 25th/75th percentiles; IQR = Q3 − Q1. Anything below
   `Q1 − 1.5·IQR` or above `Q3 + 1.5·IQR` is flagged. Distribution-free, robust — the
   default box-plot rule.
2. **Z-score method.** `z = (x − mean) / std`; flag `|z| > 3` (more than 3 SDs from the
   mean). Assumes roughly normal data, so it's less reliable on skewed columns.

A row is an outlier if **either** method flags it (the union). The flags are written back
as a boolean column `<column>_is_outlier`, so follow-up questions ("what do the outliers
have in common?") become ordinary queries.

### Association matrix (`association_matrix`)
A pairwise grid of "how strongly is every column related to every other column", where each
cell is routed through the correct statistical test by dtype (see note 02). It's the
descriptive lead-in to hypothesis testing — a quick scan for what's worth investigating.

## Reading the output
- `missing_rate` near 1.0 → the column is almost empty; usually drop it.
- `skew` large and positive → consider the median, and expect non-parametric tests later.
- `n_outliers` large → either real extreme customers or data errors; investigate before
  they distort every downstream average.

## Assumptions & pitfalls
- The z-score outlier rule is itself distorted by the outliers (mean and std are not
  robust). That's exactly why IQR is included alongside it.
- Outliers are not automatically errors — a whale customer is a real, important outlier.
  Flagging ≠ deleting.
- A high-cardinality text column (names, IDs) has no meaningful mean/mode; profiling treats
  it as categorical and shows top values, which is the right read.

## Marketing / e-commerce angle
- **Data-quality gate on every client file.** The first thing you run on a client's export
  is `profile` — it instantly surfaces the missing `Customer ID`s, the negative
  `Quantity` cancellations, the currency mixed into a text field. This is what makes your
  reports trustworthy and is invisible-but-essential work.
- **"Typical order value" done honestly.** Report the median AOV, not the mean, on a
  right-skewed order table — and be able to explain why to the client.
- **Whale detection.** Outlier flagging on a spend column surfaces the handful of customers
  who drive a disproportionate share of revenue — the start of a retention conversation.
