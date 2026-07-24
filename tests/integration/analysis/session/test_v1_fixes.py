"""Regression tests for the V1-surface verification findings.

Session-bound cases only. The CLI cases live in ``integration/app/test_cli.py``,
the pure jsonable case in ``unit/shared/test_serialize.py``, and the corrupt-meta
case in ``integration/analysis/db/test_persistence.py``.

Mirrors: src/tabint/analysis/session.py (regression coverage).
"""
import pandas as pd

from tabint.analysis import persistence
from tests.unit.factory import numeric_frame


# --- #6: continuous float on a small table classifies as continuous ------- #

def test_small_table_float_is_continuous(tmp_path, csv_writer):
    df = pd.DataFrame({"grp": ["a", "b"] * 6, "measure": [float(i) + 0.5 for i in range(12)]})
    s = persistence.create_session([csv_writer(df, "d.csv")], base=tmp_path)
    r = s.table("d").analyze_association("grp", "measure")
    # 'measure' must be treated as continuous -> a group test, not chi-square
    assert r.method in {"welch_t_test", "anova", "mann_whitney", "kruskal_wallis"}


# --- #7: explain_prediction reachable from the MCP ------------------------ #

def test_mcp_exposes_explain_prediction():
    from tabint.analysis import tools as M
    assert hasattr(M, "explain_prediction")
