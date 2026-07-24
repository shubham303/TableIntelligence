"""Mock-data factory — pure pandas builders for unit tests.

These produce DataFrames in memory (no filesystem, no DuckDB). They centralise
the ad-hoc ``pd.DataFrame({...})`` blocks that were duplicated across test
files, and are the single place to reach for when a unit test needs tabular
fixture data.

Conventions:
  * Every builder is a *plain function* (not a fixture) so it can be called
    freely inside test bodies and parametrize lists. Fixtures that wrap them
    live in ``conftest.py``.
  * Numeric builders are seeded for determinism.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ── primitive column builders ──────────────────────────────────────────────

def numeric_series(n: int, *, mean: float = 0.0, std: float = 1.0, seed: int = 0) -> pd.Series:
    """Continuous Gaussian column drawn from a seeded RNG."""
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(mean, std, n))


def categorical_series(n: int, categories: list[str], *, seed: int = 0) -> pd.Series:
    """Categorical column sampled (with replacement) from `categories`."""
    rng = np.random.default_rng(seed)
    return pd.Series(rng.choice(categories, size=n))


def timestamps(n: int, *, freq: str = "D", start: str = "2024-01-01") -> pd.Series:
    """Evenly spaced timestamps as a pandas datetime column."""
    return pd.Series(pd.date_range(start, periods=n, freq=freq))


def binary_series(n: int, value: int = 1) -> pd.Series:
    """A degenerate binary column — every row is `value` (for edge-case tests)."""
    return pd.Series([value] * n)


# ── whole-frame builders ───────────────────────────────────────────────────

def make_frame(**columns) -> pd.DataFrame:
    """Assemble a DataFrame from named Series / lists. The generic escape hatch."""
    return pd.DataFrame(columns)


def numeric_frame(n: int = 40, *, ncols: int = 2, target: bool = True, seed: int = 0) -> pd.DataFrame:
    """A regression-style frame: `x1..xN` numeric features plus an optional `y`."""
    rng = np.random.default_rng(seed)
    data = {f"x{i}": rng.normal(size=n) for i in range(1, ncols + 1)}
    if target:
        data["y"] = ([0, 1] * n)[:n]  # balanced binary target
    return pd.DataFrame(data)


def churn_frame(n: int = 40, *, seed: int = 0) -> pd.DataFrame:
    """Customer-churn-like frame: numeric + categorical features + binary target."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "age": rng.integers(18, 75, n),
        "total_spend": rng.normal(500, 100, n),
        "visits": rng.poisson(5, n),
        "tier": rng.choice(["bronze", "silver", "gold"], n),
        "is_churned": rng.integers(0, 2, n),
    })


def loan_frame(n: int = 60, *, with_nan_target: bool = False, seed: int = 0) -> pd.DataFrame:
    """Loan-application-like frame: numeric features + a classification target.

    `with_nan_target` injects a couple of NaNs into the target column (the
    regressor-tolerates-NaN regression case).
    """
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "income": rng.normal(60000, 15000, n),
        "debt": rng.normal(20000, 8000, n),
        "score": rng.integers(300, 850, n),
        "is_approved": rng.integers(0, 2, n),
    })
    if with_nan_target:
        df.loc[3, "is_approved"] = np.nan
        df.loc[17, "is_approved"] = np.nan
    return df


def time_series_frame(n: int = 48, *, start: str = "2021-01-01", freq: str = "MS", seed: int = 0) -> pd.DataFrame:
    """A monthly time series: a date column and a single value column."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "month": pd.date_range(start, periods=n, freq=freq).astype(str),
        "sales": rng.normal(100, 15, n).cumsum(),
    })


def constant_continuous_frame(*, n: int = 6) -> pd.DataFrame:
    """A degenerate frame whose continuous column is constant — for edge cases."""
    return pd.DataFrame({"grp": ["a"] * (n // 2) + ["b"] * (n - n // 2), "val": [5.0] * n})


def two_group_numeric_frame(g1, g2, *, g1_name: str = "A", g2_name: str = "B") -> pd.DataFrame:
    """Two-group continuous frame from raw arrays (unequal-variance test case)."""
    rows = [[g1_name, v] for v in g1] + [[g2_name, v] for v in g2]
    return pd.DataFrame(rows, columns=["grp", "val"])
