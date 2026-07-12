# 08 — Supervised learning (prediction)

Code: `analytics/supervised.py` — `train_classifier`, `train_regressor`, `evaluate`
(+ `TrainedModel`). Library: scikit-learn (HistGradientBoosting default; TabICL optional).

## Intuition
Supervised learning = "learn to predict a **target** column Y from feature columns X, using
historical rows where you already know Y." Two flavours by the type of Y:
- **Classification** — Y is a category (will this customer churn? yes/no).
- **Regression** — Y is a number (what will this order be worth?).

## The workflow the code enforces (and why each step matters)
1. **Feature/target split**, dropping rows with a missing target (can't learn from an
   unknown answer).
2. **Preprocessing in a Pipeline** — impute missing values + one-hot encode categoricals,
   bundled *with* the model so new rows are transformed identically at predict time. This
   prevents **train/serve skew** (the classic bug where prod data is prepped differently
   from training data).
3. **Train/test split** (75/25), *stratified* for classification so both classes appear in
   both splits. **The model is scored only on the held-out 25% it never saw** — the single
   most important discipline in ML. Scoring on training data gives a flattering lie.
4. **Fit**, then wrap everything in a `TrainedModel` that also carries the test split for
   honest evaluation and interpretation (note 09).

## The two backends
- **`gbt` (default)** — HistGradientBoosting: an ensemble of decision trees built
  sequentially, each correcting the last's errors. The strong, reliable default for tabular
  data; no GPU, scales to any size.
- **`tabicl`** — a tabular **foundation model** (a pre-trained transformer that predicts via
  in-context learning — *one forward pass, no per-task training*). Often beats tuned trees
  on small/medium tables out of the box. Opt-in "power lane"; GPU-recommended; refuses early
  above ~500k rows / ~2k features. This is the modern, differentiated capability.

## Reading the metrics (`evaluate`)
**Classification:**
- **Accuracy** — % correct. *Misleading on imbalanced data* — if 2% churn, predicting
  "nobody churns" scores 98%.
- **Precision** — of those you flagged positive, how many really were. (Cost of false
  alarms.)
- **Recall** — of the true positives, how many you caught. (Cost of misses.)
- **F1** — the harmonic mean of precision and recall; the honest single number when classes
  are imbalanced.
- **ROC-AUC** — probability the model ranks a random positive above a random negative;
  0.5 = coin-flip, 1.0 = perfect. Good threshold-independent summary.
- **Confusion matrix** — the raw counts of right/wrong per class.

**Regression:**
- **MAE** — average absolute error, in the target's units (easy to explain to a client).
- **RMSE** — like MAE but punishes big misses more.
- **R²** — share of the target's variance explained; 1.0 = perfect, 0 = no better than
  predicting the mean, negative = worse than the mean.

## Pitfalls
- **Overfitting** — a model that aces training data and fails on new data. The held-out
  split is the guard; always quote test metrics.
- **Imbalanced classes** — lead with F1/ROC-AUC, not accuracy.
- **Leakage** — a feature that secretly encodes the answer (e.g. "cancellation_date" when
  predicting churn) → unbelievably good scores that collapse in production. Audit features.
- A prediction is **not** a cause — see note 10. High feature importance ≠ "change this to
  move the outcome."

## Marketing / e-commerce angle
- **Churn prediction** (classification): flag customers likely to lapse *before* they do →
  a targeted retention campaign. The deliverable a client can't make themselves.
- **Lead scoring** (classification): rank inbound leads by conversion probability so the
  client spends sales time where it pays.
- **CLV / order-value prediction** (regression): estimate a customer's forward value to set
  acquisition budgets.
Needs history and volume — a retainer-tier tool. For a small client, stay in notes 03–04.
