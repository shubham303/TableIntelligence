"""Time series family — OPTIONAL.

Applicable when the table has a time axis (a datetime column that orders the
rows). decompose splits a series into trend / seasonality / residual; forecast
projects it forward. Library: statsmodels (seasonal_decompose, ARIMA). Prophet
is a possible future lazy path.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose

from ..results import Result


def decompose(store: Any, time_column: str, value_column: str) -> Result:
    """Decompose a time series into trend, seasonality, and residual.

    Args:
        store: The Store instance holding the table.
        time_column: Name of the datetime column (the time axis).
        value_column: Name of the numeric column to decompose.
        period is inferred from the series length (falls back to 2).

    Returns:
        Result with trend, seasonality, and residual arrays and the period used.
    """
    series = _ordered_series(store, time_column, value_column)
    if series.size < 4:
        raise ValueError(
            f"decompose needs at least 4 valid observations; {value_column} has {series.size}."
        )
    # seasonal_decompose requires >= 2*period points; never let the period exceed
    # what the (possibly short) series can support.
    period = min(_infer_period(series), series.size // 2)
    result = seasonal_decompose(series, model="additive", period=period, extrapolate_trend="freq")

    return Result(
        method="seasonal_decompose",
        summary=f"Decomposed {value_column} (additive, period={period})",
        values={
            "trend": _clean_list(result.trend),
            "seasonal": _clean_list(result.seasonal),
            "residual": _clean_list(result.resid),
        },
        metadata={
            "time_column": time_column,
            "value_column": value_column,
            "period": period,
            "model": "additive",
            "n_points": int(series.size),
        },
    )


def forecast(
    store: Any,
    time_column: str,
    value_column: str,
    horizon: int = 10,
) -> Result:
    """Forecast future values with an ARIMA model.

    Args:
        store: The Store instance holding the table.
        time_column: Name of the datetime column.
        value_column: Name of the numeric column to forecast.
        horizon: Number of future periods to forecast.

    Returns:
        Result with point forecasts, 95% confidence intervals, and the ARIMA order.
    """
    series = _ordered_series(store, time_column, value_column)
    order = (1, 1, 1)
    model = ARIMA(series.to_numpy(), order=order).fit()
    fc = model.get_forecast(steps=horizon)
    mean = fc.predicted_mean
    ci = fc.conf_int(alpha=0.05)

    return Result(
        method="arima",
        summary=f"{horizon}-step forecast of {value_column} (ARIMA{order})",
        values={
            "forecast": [float(v) for v in mean],
            "lower": [float(v) for v in ci[:, 0]],
            "upper": [float(v) for v in ci[:, 1]],
        },
        metadata={
            "time_column": time_column,
            "value_column": value_column,
            "order": list(order),
            "horizon": horizon,
        },
    )


def _ordered_series(store: Any, time_column: str, value_column: str) -> pd.Series:
    """Return the value column as a numeric Series ordered by the time column."""
    frame = store.get_frame()[[time_column, value_column]].copy()
    frame[time_column] = pd.to_datetime(frame[time_column], errors="coerce")
    frame = frame.dropna().sort_values(time_column)
    series = pd.to_numeric(frame[value_column], errors="coerce").dropna()
    series.index = frame.loc[series.index, time_column]
    return series.reset_index(drop=True)


def _infer_period(series: pd.Series) -> int:
    """A conservative seasonal period: enough data for two full cycles, else 2."""
    n = series.size
    for candidate in (12, 7, 4):
        if n >= 2 * candidate:
            return candidate
    return max(2, n // 2)


def _clean_list(arr: Any) -> list[float]:
    return [None if pd.isna(v) else float(v) for v in np.asarray(arr)]
