"""Time series family — OPTIONAL.

Only applicable when the table has a time axis (a datetime column that is
the primary ordering key). Build only if tables with a time axis are a
target use case.

Planned functions: decompose, forecast.
Libraries (planned, not yet imported): statsmodels, prophet.
"""
from __future__ import annotations

from typing import Any

# planned: from statsmodels.tsa.seasonal import seasonal_decompose
# planned: from prophet import Prophet


def decompose(store: Any, time_column: str, value_column: str) -> Any:
    """Decompose a time series into trend, seasonality, and residual components.

    Args:
        store: The Store instance holding the table.
        time_column: Name of the datetime column (the time axis).
        value_column: Name of the numeric column to decompose.

    Returns:
        Result with trend, seasonality, and residual arrays, plus the period detected.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")


def forecast(
    store: Any,
    time_column: str,
    value_column: str,
    horizon: int = 10,
) -> Any:
    """Forecast future values of a time series.

    Args:
        store: The Store instance holding the table.
        time_column: Name of the datetime column.
        value_column: Name of the numeric column to forecast.
        horizon: Number of future periods to forecast.

    Returns:
        Result with point forecasts, confidence intervals, and the model used.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
