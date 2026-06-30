"""Descriptive / exploratory analytics family.

Planned functions: profile, detect_outliers, association_matrix.
Libraries (planned, not yet imported): pandas, numpy.
"""
from __future__ import annotations

from typing import Any

# planned: import pandas as pd
# planned: import numpy as np


def profile(store: Any) -> Any:
    """Profile every column in the table.

    Reports per-column: type, distribution shape, missingness rate, cardinality,
    value range, and sample values. Foundation for all subsequent analysis and the
    context a future agent reads to understand a table.

    Args:
        store: The Store instance holding the table.

    Returns:
        Result with per-column statistics dict.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")


def detect_outliers(store: Any, column: str) -> Any:
    """Detect outliers in a numeric column using IQR and z-score methods.

    Args:
        store: The Store instance holding the table.
        column: Name of the numeric column to analyze.

    Returns:
        Result with row-level outlier flags and the thresholds used.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")


def association_matrix(store: Any) -> Any:
    """Compute pairwise associations across all column pairs.

    Each pair uses the measure appropriate to its dtype combination
    (see analytics/association.py for routing logic). The result is a
    symmetric matrix of association strength values.

    Args:
        store: The Store instance holding the table.

    Returns:
        Result with association matrix and the measure used per pair.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
