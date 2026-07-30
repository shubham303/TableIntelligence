"""Tests for the generic feature-computation family.

Feature functions *create* columns; the invariants under test are: the column is
written with correct values, and it is model-eligible (feature=True) rather than
excluded as a derived annotation.

Mirrors: src/tabint/analysis/service/algorithms/feature_computation.py
"""
import numpy as np
import pytest

from tabint import Session
from tabint.analysis.service import _prep
from tabint.analysis.service.algorithms import feature_computation as fc


def _table(s: Session):
    return s.table(s.tables[0])


def _features(store):
    # Newly-derived categorical columns (bins, etc.) start unclassified; mock the
    # LLM step so feature_columns can run (it errors on bare 'categorical').
    store.classify_categorical_as_nominal()
    num, nominal, ordinal = _prep.feature_columns(store)
    return set(num) | set(nominal) | set(ordinal)


# --------------------------------------------------------------------------- #
# combine_columns
# --------------------------------------------------------------------------- #

def test_combine_columns_ratio_and_is_feature(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    r = fc.combine_columns(t, "salary", "years_at_company", "divide", name="salary_per_year")
    frame = t.get_frame()
    assert r.values["column"] == "salary_per_year"
    expected = (frame["salary"] / frame["years_at_company"]).replace(
        [np.inf, -np.inf], np.nan
    )
    np.testing.assert_allclose(frame["salary_per_year"], expected, rtol=1e-9)
    # Engineered column must be usable as a feature, not excluded as derived.
    assert "salary_per_year" in _features(t)
    assert "salary_per_year" not in t.derived_columns()


def test_combine_columns_divide_by_zero_is_nan(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    # subtract a column from itself, then divide by it → 0 denominator → NaN
    fc.combine_columns(t, "age", "age", "subtract", name="zero")
    fc.combine_columns(t, "salary", "zero", "divide", name="over_zero")
    assert t.get_frame()["over_zero"].isna().all()


def test_combine_columns_rejects_unknown_op(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    with pytest.raises(ValueError):
        fc.combine_columns(t, "salary", "age", "power")


# --------------------------------------------------------------------------- #
# transform_column
# --------------------------------------------------------------------------- #

def test_transform_log_masks_nonpositive(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    fc.combine_columns(t, "age", "age", "subtract", name="zeros")  # all zero
    r = fc.transform_column(t, "zeros", "log", name="log_zeros")
    assert r.values["n_non_null"] == 0  # log(0) is undefined → all NaN


def test_transform_zscore_is_standardized(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    fc.transform_column(t, "salary", "zscore", name="z")
    z = t.get_frame()["z"]
    assert abs(z.mean()) < 1e-9
    assert abs(z.std(ddof=0) - 1.0) < 1e-9


# --------------------------------------------------------------------------- #
# bin_column
# --------------------------------------------------------------------------- #

def test_bin_column_quantile(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    r = fc.bin_column(t, "salary", n_bins=3, name="salary_bin")
    assert r.values["n_bins"] <= 3
    assert "salary_bin" in _features(t)


# --------------------------------------------------------------------------- #
# group_aggregate
# --------------------------------------------------------------------------- #

def test_group_aggregate_broadcasts_and_deviation(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    fc.group_aggregate(t, "department", "salary", "mean", add_deviation=True)
    frame = t.get_frame()
    gmean = frame.groupby("department")["salary"].transform("mean")
    np.testing.assert_allclose(frame["salary_mean_by_department"], gmean, rtol=1e-9)
    np.testing.assert_allclose(
        frame["salary_dev_from_department"], frame["salary"] - gmean, rtol=1e-9
    )
    assert {"salary_mean_by_department", "salary_dev_from_department"} <= _features(t)


# --------------------------------------------------------------------------- #
# row_aggregate & normalize_fractions
# --------------------------------------------------------------------------- #

def test_row_aggregate_sum(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    fc.row_aggregate(t, ["age", "years_at_company"], "sum", name="total")
    frame = t.get_frame()
    np.testing.assert_allclose(frame["total"], frame["age"] + frame["years_at_company"])


def test_normalize_fractions_sum_to_one(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    fc.normalize_fractions(t, ["age", "years_at_company"])
    frame = t.get_frame()
    total = frame["age_frac"] + frame["years_at_company_frac"]
    np.testing.assert_allclose(total.dropna(), 1.0, rtol=1e-9)


def test_row_aggregate_requires_two_columns(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    with pytest.raises(ValueError):
        fc.row_aggregate(t, ["age"], "sum")


# --------------------------------------------------------------------------- #
# compute_feature — custom SQL scalar expression (the escape hatch)
# --------------------------------------------------------------------------- #

def test_compute_feature_scalar_expression_is_a_feature(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    r = t.compute_feature("salary_per_year", "salary / NULLIF(years_at_company, 0)")
    frame = t.get_frame()
    expected = frame["salary"] / frame["years_at_company"].replace(0, np.nan)
    np.testing.assert_allclose(frame["salary_per_year"], expected, rtol=1e-9)
    assert "salary_per_year" in _features(t)
    assert "salary_per_year" not in t.derived_columns()


def test_compute_feature_window_runs_in_db(session_loader):
    # A window function can't be done row-wise in pandas via this path — it proves
    # the expression is evaluated inside DuckDB over the whole table.
    s = session_loader("employees.csv")
    t = _table(s)
    t.compute_feature("dept_avg_salary", "avg(salary) OVER (PARTITION BY department)")
    frame = t.get_frame()
    expected = frame.groupby("department")["salary"].transform("mean")
    np.testing.assert_allclose(frame["dept_avg_salary"], expected, rtol=1e-9)


def test_compute_feature_replace_semantics(session_loader):
    s = session_loader("employees.csv")
    t = _table(s)
    t.compute_feature("f", "age + 1")
    t.compute_feature("f", "age + 2")  # replaces, no duplicate column
    frame = t.get_frame()
    assert list(frame.columns).count("f") == 1
    np.testing.assert_allclose(frame["f"], frame["age"] + 2)


@pytest.mark.parametrize(
    "expr",
    [
        "1); DROP TABLE _data; --",       # statement chaining
        "(SELECT 1)",                      # subquery
        "read_csv('/etc/passwd')",         # file reader
        "no_such_column + 1",              # invalid binding
        "",                                # empty
    ],
)
def test_compute_feature_rejects_unsafe_expressions(session_loader, expr):
    s = session_loader("employees.csv")
    t = _table(s)
    with pytest.raises(ValueError):
        t.compute_feature("bad", expr)
    # A rejected expression must not have created a column.
    assert "bad" not in t.get_frame().columns
