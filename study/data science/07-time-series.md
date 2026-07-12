# 07 — Time series (trend, forecast, changepoints)

Code: `analytics/timeseries.py` — `decompose`, `forecast`, `detect_changepoints`.
Libraries: statsmodels (decompose, ARIMA), **ruptures** (changepoints, optional extra).

Applies whenever the table has a **time axis** — a datetime column ordering the rows
(daily sessions, weekly revenue, monthly signups). This is where "what happened" becomes
"what's coming" and "when did it break."

## Part A — Decomposition (`decompose`)
### Intuition
Any time series is really three things added together:
`observed = trend + seasonality + residual`.
- **Trend** — the slow underlying direction (are we growing?).
- **Seasonality** — the repeating pattern (weekends dip, December spikes).
- **Residual** — what's left (noise + one-off events).
Separating them stops you mistaking "December always spikes" for real growth. Uses
statsmodels `seasonal_decompose` (additive); the seasonal period is inferred conservatively
(12/7/4) from series length.

## Part B — Forecasting (`forecast`)
### Intuition
Project the series forward. Uses **ARIMA(1,1,1)** — a standard classical model:
- **AR (AutoRegressive)** — next value depends on recent values.
- **I (Integrated)** — model the *change* between steps, which removes a trend and makes
  the series stationary (statistically stable over time).
- **MA (Moving Average)** — next value depends on recent forecast errors.
Returns point forecasts **plus a 95% confidence interval** (lower/upper). The interval is
the honest part: it says "here's the range, not a false-precision single number."

### Pitfalls
- ARIMA(1,1,1) is a sane default, not a tuned model — it captures trend + short memory, but
  not strong seasonality (SARIMA/Prophet would). Say so rather than over-trusting it.
- **Forecasts assume the future behaves like the past.** A campaign, a viral moment, or a
  policy change breaks that — always caveat with the confidence interval.
- Needs enough history; a dozen points can't forecast a quarter credibly.

## Part C — Changepoint detection (`detect_changepoints`)
### Intuition
"When exactly did the metric's behaviour *change*?" Not a gradual trend — a structural
break: the level shifts and stays shifted. Uses **ruptures PELT with an RBF cost**, which
finds the break points that best explain the series, and returns the change *dates* plus
each segment's mean.
- The `penalty` controls sensitivity: higher → fewer, more confident changepoints.
- Output reads like "mean dropped from 1,200 to 780 after 2026-03-14."

### Pitfalls
- Too-low penalty invents breaks in noise; too-high misses real ones. Tune it.
- It finds *when*, never *why* — you line the date up against a known event (algo update,
  tracking change, budget cut) to form the hypothesis.

## Marketing / e-commerce angle
- **Decompose**: separate a client's real SEO growth from seasonal swings, so you don't take
  credit for December or blame yourself for January.
- **Forecast**: "at current trajectory you land at ~X next quarter (range A–B)" — the
  forward number that justifies next quarter's budget.
- **Changepoints**: the highest-value one for agencies — "organic traffic structurally
  broke on the 14th," which you then align with a Google update or a tracking failure.
  It turns a vague "traffic's been weird" into a dated, investigable event.
