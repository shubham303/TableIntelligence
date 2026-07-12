# 03 — Comparing periods ("what changed, and is it real?")

Code: `analytics/compare.py` — `compare_periods`. Library: scipy.stats.
This is the backbone of any recurring "this month vs last month" engagement — the single
most repeated deliverable an agency produces.

## Intuition
A client says "traffic dropped this month." The naive answer compares two averages. The
*honest* answer also asks: is the drop bigger than normal week-to-week noise, or is it real?
`compare_periods` splits a metric at a cut date into a **before** and **after** window and
quantifies the shift with both a size and a significance.

## What it computes
Given a time column, a value column, and a split date (defaults to the median timestamp so
the two windows are ~equal size):

- **mean_before, mean_after** — the two averages.
- **delta** — absolute change.
- **pct_change** — percentage change (what the client reads first).
- **Mann-Whitney U p-value** — "is the shift statistically real?" Non-parametric, so no
  normality assumption (right for skewed marketing metrics).
- **KS (Kolmogorov-Smirnov) p-value** — a complementary test asking whether the *whole
  distribution* changed, not just the average. (A metric can hold its mean while its shape
  shifts — e.g. more very-high and very-low days.)
- **Cohen's d** — the effect size: the change measured in standard-deviation units.
  Rule of thumb: 0.2 = small, 0.5 = medium, 0.8 = large.

## Reading the output
The `summary` reads like: *"revenue down −12.4% across the split (significant, p=0.003)."*
Then you look at Cohen's d to judge whether "significant" is also "big enough to act on."

- Significant (low p) **and** meaningful d → a real, report-worthy change.
- Significant but tiny d → technically real, practically noise (the big-data trap from
  note 02, again).
- Not significant → don't tell the client the metric "changed"; it moved within noise.

## Assumptions & pitfalls
- **The split date matters enormously.** Splitting at the median gives equal windows, but
  the interesting question is usually "did it change *after a specific event*?" — pass that
  event date as `split`. Cherry-picking a split to manufacture a finding is malpractice.
- **This is a two-window comparison, not a trend.** For gradual drift or "when exactly did
  it break", use time-series changepoints (note 07). Use `compare_periods` for a clean
  before/after around a known cut.
- Each side needs ≥ 2 points; tiny windows aren't testable.
- Still association, not causation — "revenue fell after the redesign" ≠ "the redesign
  caused it" (note 10).

## Marketing / e-commerce angle
This *is* the monthly client report's opening section, generated instead of hand-built:
- "Conversions since the **Google algorithm update on the 14th** vs before" — pass the
  update date as the split; report % change + significance.
- "AOV **this campaign period** vs the prior one."
- "Did **email revenue** actually change after we moved to the new flow, or is it noise?"
Being able to say *"the drop is significant (p=0.003) and moderate (d=0.6)"* rather than
"traffic looks down" is exactly the depth that renews a retainer.
