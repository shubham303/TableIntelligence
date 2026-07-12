"""Association / hypothesis testing family — the flagship function.

analyze_association routes to the correct test purely from the dtype pair:

    continuous × continuous:
        → Pearson correlation   (both columns pass is_normal)
        → Spearman correlation  (otherwise)

    categorical × continuous:
        → Welch's t-test        (2 groups, normal + enough samples; no equal-variance assumption)
        → One-way ANOVA         (3+ groups, normal + equal variance)
        → Mann-Whitney U        (2 groups, assumptions fail)
        → Kruskal-Wallis        (3+ groups, assumptions fail)
        → effect size: eta² (parametric) or epsilon² (non-parametric)

    categorical × categorical:
        → Chi-square            (expected cell counts OK)
        → Fisher's exact        (2×2 with small expected counts)
        → effect size: Cramér's V

The selection logic is the point; the computation is delegated to scipy.stats.
Every choice — and the assumption checks that drove it — is recorded in the
Result's metadata.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from ..results import Result
from ..validation import assumptions, dtypes

# validation.dtypes vocabulary collapsed to the two kinds association cares about.
_CATEGORICAL = {"categorical_nominal", "categorical_ordinal"}
_CONTINUOUS = {"continuous"}


def _kind(col_name: str, store: Any) -> str:
    """Collapse the fine dtype into 'continuous' or 'categorical' for routing."""
    t = dtypes.classify_column(col_name, store)
    if t in _CONTINUOUS:
        return "continuous"
    if t in _CATEGORICAL:
        return "categorical"
    # datetime / identifier are not meaningfully testable for association.
    raise ValueError(
        f"Column {col_name!r} classified as {t!r}; association is only defined "
        "for continuous and categorical columns."
    )


def analyze_association(store: Any, col_a: str, col_b: str) -> Result:
    """Analyze the statistical association between two columns.

    Args:
        store: The Store instance holding the table.
        col_a: Name of the first column.
        col_b: Name of the second column.

    Returns:
        Result with the chosen test, statistic, p-value, effect size, and the
        assumption checks that drove the selection.
    """
    if col_a == col_b:
        raise ValueError("Cannot compute the association of a column with itself.")

    frame = store.get_frame()
    kind_a, kind_b = _kind(col_a, store), _kind(col_b, store)

    if kind_a == "continuous" and kind_b == "continuous":
        return _continuous_continuous(frame, col_a, col_b)
    if kind_a == "categorical" and kind_b == "categorical":
        return _categorical_categorical(frame, col_a, col_b)
    # Exactly one of each — orient as (categorical group, continuous value).
    if kind_a == "categorical":
        return _categorical_continuous(frame, col_a, col_b)
    return _categorical_continuous(frame, col_b, col_a)


# --------------------------------------------------------------------------- #
# continuous × continuous
# --------------------------------------------------------------------------- #

def _continuous_continuous(frame: pd.DataFrame, col_a: str, col_b: str) -> Result:
    pair = frame[[col_a, col_b]].dropna()
    x, y = pair[col_a].to_numpy(float), pair[col_b].to_numpy(float)

    both_normal = assumptions.is_normal(x) and assumptions.is_normal(y)
    if both_normal:
        method = "pearson"
        r, p = stats.pearsonr(x, y)
    else:
        method = "spearman"
        r, p = stats.spearmanr(x, y)

    strength = _corr_strength(abs(r))
    direction = "positive" if r >= 0 else "negative"
    return Result(
        method=method,
        summary=f"{strength} {direction} correlation (r={r:.3f}, p={p:.3g})",
        values={
            "statistic": float(r),
            "p_value": float(p),
            "effect_size": float(abs(r)),
            "r_squared": float(r * r),
            "n": int(pair.shape[0]),
        },
        metadata={
            "dtype_a": "continuous",
            "dtype_b": "continuous",
            "effect_size_measure": "pearson_r" if both_normal else "spearman_rho",
            "assumption_checks": {"both_normal": both_normal},
        },
    )


# --------------------------------------------------------------------------- #
# categorical × continuous
# --------------------------------------------------------------------------- #

def _categorical_continuous(frame: pd.DataFrame, cat_col: str, num_col: str) -> Result:
    pair = frame[[cat_col, num_col]].dropna()
    groups = [g[num_col].to_numpy(float) for _, g in pair.groupby(cat_col, observed=True)]
    groups = [g for g in groups if g.size > 0]
    k = len(groups)
    if k < 2:
        raise ValueError(
            f"Need at least 2 non-empty groups in {cat_col!r} to test association; got {k}."
        )

    # A fully-constant value column has no variance to explain — every test
    # (mann-whitney, kruskal, and the effect-size helpers) errors or is undefined
    # on identical data, so return a degenerate "no association" result instead.
    if np.ptp(np.concatenate(groups)) == 0:
        return Result(
            method="degenerate",
            summary=f"no variance in {num_col}; association undefined",
            values={"statistic": 0.0, "p_value": 1.0, "effect_size": 0.0, "n_groups": int(k)},
            metadata={
                "dtype_a": "categorical",
                "dtype_b": "continuous",
                "effect_size_measure": "none",
                "assumption_checks": {"constant_value_column": True},
            },
        )

    normal = all(assumptions.is_normal(g) for g in groups)
    equal_var = assumptions.has_equal_variance(*groups)
    sized = assumptions.enough_samples(*groups)

    if k == 2 and normal and sized:
        # Welch's t-test: does NOT assume equal variance, so it's the robust
        # default — nearly as powerful as Student's when variances are equal and
        # correct when they aren't. Equal variance is therefore not a gate here.
        method = "welch_t_test"
        stat, p = stats.ttest_ind(groups[0], groups[1], equal_var=False)
        parametric = True
    elif k > 2 and normal and equal_var and sized:
        # Standard one-way ANOVA does assume equal variance, so keep that gate.
        method = "anova"
        stat, p = stats.f_oneway(*groups)
        parametric = True
    elif k == 2:
        method = "mann_whitney"
        stat, p = stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided")
        parametric = False
    else:
        method = "kruskal_wallis"
        stat, p = stats.kruskal(*groups)
        parametric = False

    values = {"statistic": float(stat), "p_value": float(p), "n_groups": int(k)}
    if parametric:
        effect = _eta_squared(groups)
        measure = "eta_squared"
        # omega² is the less-biased companion to eta² on the parametric path.
        omega = _omega_squared(groups)
        values["omega_squared"] = omega
        effect_note = f"eta_squared={effect:.3f}, omega_squared={omega:.3f}"
    else:
        effect = _epsilon_squared(groups)
        measure = "epsilon_squared"
        effect_note = f"{measure}={effect:.3f}"
    values["effect_size"] = float(effect)

    sig = "significant" if p < 0.05 else "no significant"
    return Result(
        method=method,
        summary=(
            f"{sig} difference in {num_col} across {cat_col} "
            f"({k} groups, {effect_note}, p={p:.3g})"
        ),
        values=values,
        metadata={
            "dtype_a": "categorical",
            "dtype_b": "continuous",
            "effect_size_measure": measure,
            "assumption_checks": {
                "all_groups_normal": normal,
                "equal_variance": equal_var,
                "enough_samples": sized,
                "parametric": parametric,
            },
        },
    )


# --------------------------------------------------------------------------- #
# categorical × categorical
# --------------------------------------------------------------------------- #

def _categorical_categorical(frame: pd.DataFrame, col_a: str, col_b: str) -> Result:
    pair = frame[[col_a, col_b]].dropna()
    table = pd.crosstab(pair[col_a], pair[col_b])
    counts = table.to_numpy()

    counts_ok = assumptions.expected_counts_ok(counts)
    is_2x2 = counts.shape == (2, 2)

    if not counts_ok and is_2x2:
        method = "fisher_exact"
        stat, p = stats.fisher_exact(counts)  # stat is the odds ratio
    else:
        method = "chi_square"
        stat, p, _, _ = stats.chi2_contingency(counts)

    v = _cramers_v(counts)
    sig = "significant" if p < 0.05 else "no significant"
    return Result(
        method=method,
        summary=(
            f"{sig} association between {col_a} and {col_b} "
            f"(Cramér's V={v:.3f}, p={p:.3g})"
        ),
        values={
            "statistic": float(stat),
            "p_value": float(p),
            "effect_size": float(v),
        },
        metadata={
            "dtype_a": "categorical",
            "dtype_b": "categorical",
            "effect_size_measure": "cramers_v",
            "table_shape": list(counts.shape),
            "assumption_checks": {"expected_counts_ok": counts_ok},
        },
    )


# --------------------------------------------------------------------------- #
# effect-size helpers (definitions computed from the same data scipy tested)
# --------------------------------------------------------------------------- #

def _eta_squared(groups: list[np.ndarray]) -> float:
    """eta² = SS_between / SS_total — proportion of variance explained by group."""
    all_vals = np.concatenate(groups)
    grand = all_vals.mean()
    ss_total = np.sum((all_vals - grand) ** 2)
    ss_between = np.sum([g.size * (g.mean() - grand) ** 2 for g in groups])
    return float(ss_between / ss_total) if ss_total > 0 else 0.0


def _omega_squared(groups: list[np.ndarray]) -> float:
    """omega² — a less-biased estimator of variance explained than eta².

    ω² = (SS_between - df_between·MS_within) / (SS_total + MS_within), the standard
    one-way (fixed-effects) form. eta² overstates the effect (it's the sample
    proportion); ω² subtracts the variance the grouping would explain by chance, so
    it's the better population estimate — notably at small n. It can come out
    slightly negative when the true effect is ~0; clamp to 0 by convention.
    """
    all_vals = np.concatenate(groups)
    n, k = all_vals.size, len(groups)
    df_between, df_within = k - 1, n - k
    if df_within <= 0:
        return 0.0
    grand = all_vals.mean()
    ss_total = np.sum((all_vals - grand) ** 2)
    ss_between = np.sum([g.size * (g.mean() - grand) ** 2 for g in groups])
    ms_within = (ss_total - ss_between) / df_within
    denom = ss_total + ms_within
    if denom <= 0:
        return 0.0
    return float(max(0.0, (ss_between - df_between * ms_within) / denom))


def _epsilon_squared(groups: list[np.ndarray]) -> float:
    """epsilon² for Kruskal/Mann-Whitney: H / (n - 1), rank-based (Tomczak 2014).

    This is the standard epsilon-squared effect size, bounded in [0, 1]; not to be
    confused with the H-based eta² = (H - k + 1) / (n - k).
    """
    n = sum(g.size for g in groups)
    if n <= 1:
        return 0.0
    h, _ = stats.kruskal(*groups)
    return float(min(1.0, max(0.0, h / (n - 1))))


def _cramers_v(counts: np.ndarray) -> float:
    """Cramér's V = sqrt(chi² / (n * (min(r, c) - 1))) — association strength 0..1."""
    chi2, _, _, _ = stats.chi2_contingency(counts)
    n = counts.sum()
    min_dim = min(counts.shape) - 1
    if n == 0 or min_dim == 0:
        return 0.0
    return float(np.sqrt(chi2 / (n * min_dim)))


def _corr_strength(r_abs: float) -> str:
    if r_abs < 0.1:
        return "negligible"
    if r_abs < 0.3:
        return "weak"
    if r_abs < 0.5:
        return "moderate"
    if r_abs < 0.7:
        return "strong"
    return "very strong"
