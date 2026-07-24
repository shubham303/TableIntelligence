"""Regression tests for the deep-review findings — one (or more) per fixed defect.

Real-Session regression cases. The pure-function regression cases (#6 SHAP
aggregation, #11 epsilon-squared) live under
``unit/analysis/service/algorithms/``.

Mirrors: src/tabint/analysis/session.py (regression coverage for the
end-to-end Session surface).
"""
import json

import numpy as np
import pandas as pd
import pytest

from tabint import Session
from tests.conftest import write_csv


def _csv(base, name: str, df: pd.DataFrame) -> str:
    """File-local delegate to the shared ``write_csv`` helper.

    Kept because these regression tests build many inline DataFrames (and one
    writes into a subdirectory, not tmp_path); the shared ``csv_writer`` fixture
    always targets tmp_path, so calling ``write_csv`` directly is simpler here.
    """
    return write_csv(df, base, name)


# --- #1: regressor tolerates NaN targets ---------------------------------- #

def test_train_regressor_with_nan_target(tmp_path):
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"x1": rng.normal(size=40), "x2": rng.normal(size=40),
                       "price": rng.normal(100, 10, 40)})
    df.loc[3, "price"] = np.nan
    df.loc[17, "price"] = np.nan
    s = Session.load(_csv(tmp_path, "reg.csv", df))
    model = s.train_regressor("price")           # must not raise
    assert s.evaluate("price").values["r2"] is not None


# --- #2: independent sessions are isolated -------------------------------- #

def test_sessions_are_isolated(tmp_path):
    df = pd.DataFrame({"a": range(20), "b": np.arange(20) * 2.0,
                       "y": ([0, 1] * 10)})
    path = _csv(tmp_path, "iso.csv", df)
    s1 = Session.load(path)
    s1.cluster(n_clusters=2)
    s1.train_classifier("y", name="m1")

    s2 = Session.load(path)
    assert list(s2.models) == []                 # no leaked model
    assert "cluster" not in s2.table(s2.tables[0]).get_frame().columns  # no leaked column


# --- #3 / #8: identifiers with spaces / reserved words work --------------- #

def test_write_back_column_name_with_space(tmp_path):
    rng = np.random.default_rng(1)
    vals = list(rng.normal(100, 10, 60)) + [9999.0]
    df = pd.DataFrame({"id": range(61), "total spend": vals})
    s = Session.load(_csv(tmp_path, "spaces.csv", df))
    r = s.detect_outliers("total spend")         # must not raise
    assert r.metadata["flag_column"] == "total spend_is_outlier"


def test_reserved_word_filename_loads(tmp_path):
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    s = Session.load(_csv(tmp_path, "order.csv", df))   # 'order' is reserved
    assert s.tables == ["order_tbl"]
    assert len(s.table("order_tbl").get_frame()) == 3


# --- #4: length-mismatch write-back raises instead of truncating ---------- #

def test_write_back_length_mismatch_raises(tmp_path):
    df = pd.DataFrame({"a": range(10)})
    s = Session.load(_csv(tmp_path, "len.csv", df))
    tbl = s.table(s.tables[0])
    with pytest.raises(ValueError):
        tbl.write_back_column("c", [1, 2, 3])    # 3 values, 10 rows
    assert len(tbl.get_frame()) == 10            # table intact


# --- #5: constant continuous column -> degenerate, no crash --------------- #

def test_constant_value_column_association(tmp_path):
    df = pd.DataFrame({"grp": ["a", "a", "a", "b", "b", "b"], "val": [5.0] * 6})
    s = Session.load(_csv(tmp_path, "const.csv", df))
    r = s.analyze_association("grp", "val")      # must not raise
    assert r.values["effect_size"] == 0.0


# --- #7: CSV path containing an apostrophe loads -------------------------- #

def test_path_with_apostrophe(tmp_path):
    d = tmp_path / "O'Brien"
    d.mkdir()
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    s = Session.load(_csv(d, "data.csv", df))
    assert len(s.run_sql(f"SELECT * FROM {s.tables[0]}")) == 2


# --- #9: unrelated surrogate keys don't fabricate FK edges ---------------- #

def test_no_false_fk_between_unrelated_ids(tmp_path):
    a = _csv(tmp_path, "a.csv", pd.DataFrame({"id": range(1, 101), "aval": range(1, 101)}))
    b = _csv(tmp_path, "b.csv", pd.DataFrame({"id": range(1, 501), "bval": range(1, 501)}))
    s = Session.load([a, b])
    graph = s.relationships()
    assert graph.relationships == []             # no spurious id -> id edge


def test_real_fk_still_detected(tmp_path):
    cust = _csv(tmp_path, "customers.csv", pd.DataFrame({"customer_id": [1, 2, 3], "name": list("xyz")}))
    orders = _csv(tmp_path, "orders.csv",
                  pd.DataFrame({"order_id": [10, 11, 12, 13], "customer_id": [1, 2, 1, 3]}))
    s = Session.load([cust, orders])
    edges = {(r.child_table, r.child_column, r.parent_table, r.parent_column)
             for r in s.relationships().relationships}
    assert ("orders", "customer_id", "customers", "customer_id") in edges


# --- #10: short series decompose raises a clear error --------------------- #

def test_decompose_short_series_raises(tmp_path):
    df = pd.DataFrame({"t": pd.date_range("2021-01-01", periods=3, freq="MS").astype(str),
                       "v": [1.0, 2.0, 3.0]})
    s = Session.load(_csv(tmp_path, "ts.csv", df))
    with pytest.raises(ValueError):
        s.decompose("t", "v")


# --- #12: no fabricated silhouette on a 2-row auto-k ---------------------- #

def test_two_row_cluster_silhouette_none(tmp_path):
    df = pd.DataFrame({"a": [1.0, 5.0], "b": [2.0, 9.0]})
    s = Session.load(_csv(tmp_path, "two.csv", df))
    r = s.cluster()                              # auto-k, n_samples == 2
    assert r.values["silhouette"] is None


# --- #13: association_matrix serializes to valid JSON --------------------- #

def test_association_matrix_json_valid(tmp_path):
    # constant categorical -> analyze_association raises -> cell stays None
    df = pd.DataFrame({"grp": ["A"] * 20, "val": [float(i) for i in range(20)],
                       "val2": [i * 2.3 for i in range(20)]})
    s = Session.load(_csv(tmp_path, "mat.csv", df))
    r = s.table(s.tables[0]).association_matrix()
    dumped = json.dumps(r.model_dump())          # bare NaN would be produced by np.nan
    assert "NaN" not in dumped
    json.loads(dumped)                           # strict parse must succeed


# --- #14: tiny table / too-many-clusters are guarded ---------------------- #

def test_single_row_cluster_degenerate(tmp_path):
    df = pd.DataFrame({"a": [1.0], "b": [2.0]})
    s = Session.load(_csv(tmp_path, "one.csv", df))
    r = s.cluster()
    assert r.values["n_clusters"] == 1


def test_too_many_clusters_raises(tmp_path):
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
    s = Session.load(_csv(tmp_path, "three.csv", df))
    with pytest.raises(ValueError):
        s.cluster(n_clusters=5)
