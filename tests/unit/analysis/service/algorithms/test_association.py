"""Unit tests for the association family's effect-size helpers.

_epsilon_squared is a pure function over group arrays; the DuckDB layer is not
involved. Exercises the H/(n-1) formula.

Mirrors: src/tabint/analysis/service/algorithms/association.py
(originally test_fixes.py #11)
"""
import numpy as np
import pytest
from scipy import stats


def test_epsilon_squared_formula():
    from tabint.analysis.service.algorithms import association as A

    rng = np.random.default_rng(0)
    groups = [rng.normal(0, 1, 10), rng.normal(1, 1, 10), rng.normal(2, 1, 10)]
    h, _ = stats.kruskal(*groups)
    n = 30
    assert A._epsilon_squared(groups) == pytest.approx(h / (n - 1))
