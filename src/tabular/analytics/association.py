"""Association / hypothesis testing family.

Planned functions: analyze_association.
Libraries (planned, not yet imported): scipy.stats, statsmodels.

This is the flagship function and template for the whole library. Its
dtype-routing logic is the conceptual heart of the library:

    continuous × continuous:
        → Pearson correlation (if both columns pass is_normal)
        → Spearman correlation (otherwise)

    categorical × continuous:
        → Independent t-test (2 groups, assumptions hold: normality + equal variance)
        → One-way ANOVA (3+ groups, assumptions hold)
        → Mann-Whitney U (2 groups, assumptions fail)
        → Kruskal-Wallis (3+ groups, assumptions fail)
        → Effect size always reported: eta² (parametric) or epsilon² (non-parametric)

    categorical × categorical:
        → Chi-square test (if expected_counts_ok)
        → Fisher's exact test (otherwise, typically for 2×2 tables)
        → Cramér's V reported as effect size in both cases

The *selection logic* is the lesson here — not the computation, which is
delegated entirely to scipy/statsmodels. Every choice is reported in the
Result's metadata so the caller knows what was picked and why.
"""
from __future__ import annotations

from typing import Any

# planned: from scipy import stats
# planned: import statsmodels.stats.api as sms


def analyze_association(store: Any, col_a: str, col_b: str) -> Any:
    """Analyze the statistical association between two columns.

    Selects the appropriate test automatically based on the dtype pair
    (see module docstring for the full routing table). Reports the chosen
    test, its statistic, p-value, effect size, and the assumption checks
    that drove the selection.

    Args:
        store: The Store instance holding the table.
        col_a: Name of the first column.
        col_b: Name of the second column.

    Returns:
        Result with fields:
            method: the test name (e.g., "pearson", "kruskal_wallis")
            summary: one-line plain-language description
            values: {"statistic": ..., "p_value": ..., "effect_size": ...}
            metadata: {"dtype_a": ..., "dtype_b": ..., "assumption_checks": {...}}
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
