"""Unit tests for the SHAP one-hot aggregation helper.

_aggregate_to_columns is a pure function over a fitted sklearn preprocessor; no
DuckDB is involved. The fitted transformer is the only collaborator.

Mirrors: src/tabint/analysis/service/algorithms/interpretation.py
(originally test_fixes.py #6)
"""
import numpy as np
import pandas as pd
import pytest


def test_shap_aggregation_no_prefix_collision():
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder
    from tabint.analysis.service.algorithms.interpretation import _aggregate_to_columns

    df = pd.DataFrame({"a": ["b", "c", "b", "c"], "a_b": ["x", "y", "x", "y"]})
    cat = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    pre = ColumnTransformer([("nominal", cat, ["a", "a_b"])], remainder="drop").fit(df)
    names = list(pre.get_feature_names_out())
    vals = np.arange(1, len(names) + 1, dtype=float)
    totals = _aggregate_to_columns(pre, vals, [], ["a", "a_b"], [])
    # a -> categories b,c = 1+2 = 3 ; a_b -> x,y = 3+4 = 7
    assert totals == {"a": 3.0, "a_b": 7.0}
