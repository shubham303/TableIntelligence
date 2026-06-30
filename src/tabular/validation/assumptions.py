"""Statistical assumption checks that route test selection in the association family.

These helpers answer questions like "is this column normally distributed?" or
"do these groups have equal variance?" The answers drive which test analyze_association
selects — e.g., Pearson vs. Spearman, t-test vs. Mann-Whitney, chi-square vs. Fisher.
"""
from __future__ import annotations

from typing import Any


def is_normal(series: Any) -> bool:
    """Test whether a series is approximately normally distributed.

    Uses a standard normality test (e.g., Shapiro-Wilk for small samples,
    D'Agostino-Pearson for larger ones).

    Args:
        series: A pandas Series of numeric values.

    Returns:
        True if the null hypothesis of normality cannot be rejected at α=0.05.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")


def has_equal_variance(*groups: Any) -> bool:
    """Test whether multiple groups have equal variance (homoscedasticity).

    Uses Levene's test.

    Args:
        *groups: Two or more pandas Series, one per group.

    Returns:
        True if equal variance cannot be rejected at α=0.05.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")


def enough_samples(*groups: Any, min_per_group: int = 20) -> bool:
    """Check whether each group meets the minimum sample size.

    Args:
        *groups: One or more pandas Series, one per group.
        min_per_group: Minimum required observations per group.

    Returns:
        True if every group has at least min_per_group non-null observations.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")


def expected_counts_ok(table: Any, min_expected: float = 5.0) -> bool:
    """Check whether expected cell counts are sufficient for chi-square.

    If any expected count falls below min_expected, Fisher's exact test should
    be used instead of chi-square.

    Args:
        table: A contingency table (pandas DataFrame or 2-D array).
        min_expected: Minimum acceptable expected count per cell.

    Returns:
        True if all expected counts are >= min_expected.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
