"""Column type classification — the single source of truth for dtype routing.

Every analytics function that needs to know "is this column categorical or
continuous?" must call classify_column here. No local re-implementation of
this logic is permitted. This prevents the most common source of inconsistency
in tabular analysis pipelines.
"""
from __future__ import annotations

from typing import Any

# Possible column types returned by classify_column
COLUMN_TYPES = frozenset({
    "continuous",
    "categorical_nominal",
    "categorical_ordinal",
    "datetime",
    "identifier",
})


def classify_column(series: Any) -> str:
    """Classify a single column into a canonical type.

    Args:
        series: A pandas Series to classify.

    Returns:
        One of: "continuous", "categorical_nominal", "categorical_ordinal",
        "datetime", "identifier".
    """
    raise NotImplementedError("planned: see docs/roadmap.md")


def classify_table(df: Any) -> dict[str, str]:
    """Classify every column in a DataFrame.

    Args:
        df: A pandas DataFrame.

    Returns:
        Mapping of column name → type string (same vocabulary as classify_column).
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
