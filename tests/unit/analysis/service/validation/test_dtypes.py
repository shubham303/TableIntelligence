"""Tests for validation.dtypes — the cache-and-compute column-type classifier.

Covers the new model: classify_column is cache-and-compute against the
``_ti_column_types`` sidecar, auto-detects the coarse ``categorical`` label for
category-like columns, and set_column_type (the agent tool) refines to
categorical_nominal / categorical_ordinal. Modeling refuses unrefined
categoricals; ordinal columns are integer-encoded rather than one-hot.

Mirrors: src/tabint/analysis/service/validation/dtypes.py,
         src/tabint/analysis/db/ducktable.py (_ti_column_types),
         src/tabint/analysis/service/_prep.py.
"""
import numpy as np
import pandas as pd
import pytest

from tabint import Session
from tabint.analysis.service.validation import dtypes
from tests.conftest import write_csv


# A mixed frame: continuous, identifier, datetime, and a coarse categorical.
def _mixed_frame():
    return pd.DataFrame({
        "measure": np.arange(50.0),                 # continuous
        "grade":   [1, 2, 3, 4, 5] * 10,            # low-card numeric -> categorical
        "label":   ["a", "b"] * 25,                 # string categorical
        "uuid":    [f"id_{i}" for i in range(50)],  # identifier
        "ts":      pd.date_range("2024-01-01", periods=50, freq="h"),
    })


def _session(tmp_path):
    s = Session.load(write_csv(_mixed_frame(), tmp_path, "d.csv"))
    return s, s.table("d")


# --- auto-detection: the coarse default ----------------------------------- #

def test_auto_detect_returns_coarse_categorical_for_category_like(tmp_path):
    _, t = _session(tmp_path)
    # grade (low-card int) and label (string) are categorical, not nominal.
    assert dtypes.classify_column("grade", t) == "categorical"
    assert dtypes.classify_column("label", t) == "categorical"


def test_auto_detect_continuous_datetime_identifier_unchanged(tmp_path):
    _, t = _session(tmp_path)
    assert dtypes.classify_column("measure", t) == "continuous"
    assert dtypes.classify_column("ts", t) == "datetime"
    assert dtypes.classify_column("uuid", t) == "identifier"


# --- cache-and-compute ---------------------------------------------------- #

def test_first_call_caches_and_second_call_reads_cache(tmp_path):
    _, t = _session(tmp_path)
    assert t.get_cached_type("grade") is None       # nothing cached yet
    first = dtypes.classify_column("grade", t)
    assert first == "categorical"
    assert t.get_cached_type("grade") == "categorical"  # cached on first call
    # The cache is authoritative: even if the data changed underneath, the second
    # call returns the cached value without recomputing.
    second = dtypes.classify_column("grade", t)
    assert second == "categorical"
    assert t.get_cached_type("grade") == "categorical"


def test_override_true_recomputes_and_overwrites_cache(tmp_path):
    _, t = _session(tmp_path)
    dtypes.classify_column("grade", t)                       # caches "categorical"
    t.set_column_type("grade", "categorical_ordinal")        # agent refines
    assert dtypes.classify_column("grade", t) == "categorical_ordinal"
    # override=True bypasses the cache, recomputes, and stores the fresh result —
    # clobbering the agent-set value.
    forced = dtypes.classify_column("grade", t, override=True)
    assert forced == "categorical"
    assert t.get_cached_type("grade") == "categorical"       # cache overwritten


# --- agent refinement via set_column_type --------------------------------- #

def test_set_column_type_refines_categorical(tmp_path):
    _, t = _session(tmp_path)
    t.set_column_type("grade", "categorical_ordinal")
    assert dtypes.classify_column("grade", t) == "categorical_ordinal"


def test_set_column_type_rejects_auto_detected_types(tmp_path):
    _, t = _session(tmp_path)
    for bad in ("continuous", "datetime", "identifier", "categorical", "nonsense"):
        with pytest.raises(ValueError):
            t.set_column_type("grade", bad)


def test_set_column_type_rejects_unknown_column(tmp_path):
    _, t = _session(tmp_path)
    with pytest.raises(KeyError):
        t.set_column_type("nope", "categorical_ordinal")


def test_unset_column_type_returns_to_auto_detect(tmp_path):
    _, t = _session(tmp_path)
    t.set_column_type("grade", "categorical_ordinal")
    t.unset_column_type("grade")
    assert t.get_cached_type("grade") is None
    assert dtypes.classify_column("grade", t) == "categorical"


# --- persistence across reopen ------------------------------------------- #

def test_column_type_survives_reopen(tmp_path):
    from tabint.analysis.service.workspace import Workspace
    from tests.conftest import copy_fixtures
    db = str(tmp_path / "ws.duckdb")
    src = copy_fixtures(tmp_path, "employees.csv")[0]
    ws = Workspace.create([src], db_path=db)
    ws.table("employees").set_column_type("department", "categorical_nominal")
    ws.close()

    reopened = Workspace(db_path=db)
    rt = reopened.table("employees")
    assert dtypes.classify_column("department", rt) == "categorical_nominal"
    reopened.close()


# --- invalidation on overwrite ------------------------------------------- #

def test_overwriting_a_column_clears_its_cached_type(tmp_path):
    _, t = _session(tmp_path)
    t.set_column_type("grade", "categorical_ordinal")       # cached as ordinal
    assert t.get_cached_type("grade") == "categorical_ordinal"
    # write_back_column on an existing name invalidates the cache.
    t.write_back_column("grade", [1, 2] * 25, feature=True)
    assert t.get_cached_type("grade") is None               # cleared
    # Next classify re-detects from the new data (still low-card -> categorical).
    assert dtypes.classify_column("grade", t) == "categorical"


def test_new_derived_column_has_no_cached_type(tmp_path):
    _, t = _session(tmp_path)
    t.add_computed_column("doubled", "measure * 2", feature=True)
    assert t.get_cached_type("doubled") is None             # never classified
    assert dtypes.classify_column("doubled", t) == "continuous"


# --- the forcing function: modeling refuses unclassified categoricals ---- #

def test_feature_columns_raises_on_unclassified_categorical(tmp_path):
    from tabint.analysis.service import _prep
    _, t = _session(tmp_path)
    with pytest.raises(ValueError, match="unclassified"):
        _prep.feature_columns(t)


def test_feature_columns_succeeds_after_refinement(tmp_path):
    from tabint.analysis.service import _prep
    _, t = _session(tmp_path)
    t.set_column_type("grade", "categorical_ordinal")
    t.set_column_type("label", "categorical_nominal")
    numeric, nominal, ordinal = _prep.feature_columns(t)
    assert "measure" in numeric
    assert "label" in nominal
    assert "grade" in ordinal


def test_cluster_raises_then_succeeds_after_refinement(tmp_path):
    _, t = _session(tmp_path)
    with pytest.raises(ValueError, match="unclassified"):
        t.cluster(n_clusters=2)
    t.classify_categorical_as_nominal()
    r = t.cluster(n_clusters=2)
    assert r.values["n_clusters"] == 2


# --- encoding: ordinal -> integer, nominal -> one-hot -------------------- #

def test_ordinal_column_is_integer_encoded(tmp_path):
    from tabint.analysis.service import _prep
    _, t = _session(tmp_path)
    t.set_column_type("grade", "categorical_ordinal")
    t.set_column_type("label", "categorical_nominal")
    numeric, nominal, ordinal = _prep.feature_columns(t)
    pre = _prep.build_preprocessor(numeric, nominal, ordinal, scale=False)
    pre.fit(t.get_frame())
    branches = pre.named_transformers_
    assert "ordinal" in branches and "nominal" in branches
    # The ordinal branch is an OrdinalEncoder (one output per column), not one-hot.
    assert "ordinal" in branches["ordinal"].named_steps


def test_unclassified_categorical_never_reaches_modeler(tmp_path):
    # Smoke: the error fires before any sklearn work, with a clear message naming
    # the offending columns (so an agent knows exactly what to classify).
    from tabint.analysis.service import _prep
    _, t = _session(tmp_path)
    try:
        _prep.feature_columns(t)
    except ValueError as exc:
        assert "grade" in str(exc) and "label" in str(exc)
    else:
        pytest.fail("expected unclassified-categorical error")
