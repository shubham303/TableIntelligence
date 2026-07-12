"""Cohort family — RFM segmentation and retention curves for transaction tables.

These are the standard e-commerce / SaaS insight primitives:

* ``rfm`` — score every customer on Recency, Frequency, Monetary (quintiles) and
  bucket them into the canonical named segments (Champions, At Risk, …).
* ``retention_cohorts`` — a first-purchase-month × months-since retention matrix.

Both are textbook pandas aggregations (groupby + qcut + pivot), so we use pandas
directly rather than a heavier library — there is no dominant third-party package
for these that does more than orchestrate the same pandas calls. (CLV modelling,
which *does* warrant a library, is a separate future primitive.)
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from ..results import Result

# Canonical RFM segment map, keyed by (R-score-high?, FM-score-high?). Kept small and
# transparent — the industry-standard buckets, not a bespoke scheme.
_SEGMENTS = [
    ("Champions", lambda r, fm: r >= 4 and fm >= 4),
    ("Loyal", lambda r, fm: r >= 3 and fm >= 3),
    ("Potential Loyalist", lambda r, fm: r >= 4 and fm >= 1),
    ("At Risk", lambda r, fm: r <= 2 and fm >= 3),
    ("Hibernating", lambda r, fm: r <= 2 and fm <= 2),
]


def _segment(r: int, fm: int) -> str:
    for name, rule in _SEGMENTS:
        if rule(r, fm):
            return name
    return "Others"


def _score(series: pd.Series, reverse: bool = False) -> pd.Series:
    """Quintile score 1–5; ``reverse`` gives high scores to low values (recency)."""
    labels = [5, 4, 3, 2, 1] if reverse else [1, 2, 3, 4, 5]
    try:
        return pd.qcut(series.rank(method="first"), 5, labels=labels).astype(int)
    except ValueError:
        # Too few distinct values for 5 bins — fall back to a coarse rank.
        return pd.Series(
            pd.qcut(series.rank(method="first"), min(5, series.nunique()),
                    labels=False, duplicates="drop"),
            index=series.index,
        ).fillna(0).astype(int) + 1


def rfm(store: Any, customer_column: str, date_column: str, monetary_column: str) -> Result:
    """Score customers on Recency/Frequency/Monetary and assign named segments.

    Args:
        store: The Store/Table instance.
        customer_column: Column identifying a customer.
        date_column: Datetime column of each transaction.
        monetary_column: Numeric spend column.

    Returns:
        Result with ``segments`` (segment → customer count), ``segment_value``
        (segment → total monetary), and overall RFM ranges.
    """
    frame = store.get_frame()
    for col in (customer_column, date_column, monetary_column):
        if col not in frame.columns:
            raise ValueError(f"Column {col!r} not in table.")

    df = frame[[customer_column, date_column, monetary_column]].copy()
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
    df[monetary_column] = pd.to_numeric(df[monetary_column], errors="coerce")
    df = df.dropna()
    if df.empty:
        raise ValueError("No complete rows across customer, date, and monetary columns.")

    snapshot = df[date_column].max() + pd.Timedelta(days=1)
    agg = df.groupby(customer_column).agg(
        recency=(date_column, lambda s: (snapshot - s.max()).days),
        frequency=(date_column, "count"),
        monetary=(monetary_column, "sum"),
    )

    agg["R"] = _score(agg["recency"], reverse=True)
    agg["F"] = _score(agg["frequency"])
    agg["M"] = _score(agg["monetary"])
    agg["FM"] = ((agg["F"] + agg["M"]) / 2).round().astype(int)
    agg["segment"] = [_segment(r, fm) for r, fm in zip(agg["R"], agg["FM"])]

    seg_counts = agg["segment"].value_counts().to_dict()
    seg_value = agg.groupby("segment")["monetary"].sum().round(2).to_dict()
    top_seg = max(seg_value, key=seg_value.get) if seg_value else None

    return Result(
        method="rfm_quintile_segmentation",
        summary=(
            f"{len(agg)} customers segmented; top segment by value: {top_seg!r}"
            if top_seg else f"{len(agg)} customers segmented"
        ),
        values={
            "segments": {k: int(v) for k, v in seg_counts.items()},
            "segment_value": {k: float(v) for k, v in seg_value.items()},
        },
        metadata={
            "customer_column": customer_column,
            "date_column": date_column,
            "monetary_column": monetary_column,
            "n_customers": int(len(agg)),
            "snapshot_date": snapshot.isoformat(),
        },
    )


def retention_cohorts(store: Any, customer_column: str, date_column: str) -> Result:
    """Monthly retention matrix: first-purchase cohort × months-since-first.

    Args:
        store: The Store/Table instance.
        customer_column: Column identifying a customer.
        date_column: Datetime column of each activity/transaction.

    Returns:
        Result with ``cohorts`` (cohort month → {months_since: retained_customers})
        and ``retention_rates`` (same, as fractions of the cohort size).
    """
    frame = store.get_frame()
    for col in (customer_column, date_column):
        if col not in frame.columns:
            raise ValueError(f"Column {col!r} not in table.")

    df = frame[[customer_column, date_column]].copy()
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
    df = df.dropna()
    if df.empty:
        raise ValueError("No complete rows across customer and date columns.")

    df["period"] = df[date_column].dt.to_period("M")
    df["cohort"] = df.groupby(customer_column)[date_column].transform("min").dt.to_period("M")
    df["months_since"] = (
        (df["period"].dt.year - df["cohort"].dt.year) * 12
        + (df["period"].dt.month - df["cohort"].dt.month)
    )

    counts = (
        df.groupby(["cohort", "months_since"])[customer_column]
        .nunique()
        .reset_index()
    )
    matrix = counts.pivot(index="cohort", columns="months_since", values=customer_column)
    sizes = matrix[0]
    rates = matrix.div(sizes, axis=0)

    def _fmt(m: pd.DataFrame) -> dict:
        return {
            str(cohort): {int(k): (None if pd.isna(v) else float(v))
                          for k, v in row.items() if not pd.isna(v)}
            for cohort, row in m.iterrows()
        }

    return Result(
        method="monthly_retention_cohorts",
        summary=f"{len(matrix)} monthly cohorts, up to {int(matrix.columns.max())} months tracked",
        values={"cohorts": _fmt(matrix), "retention_rates": _fmt(rates.round(4))},
        metadata={
            "customer_column": customer_column,
            "date_column": date_column,
            "n_cohorts": int(len(matrix)),
        },
    )
