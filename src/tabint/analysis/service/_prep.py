"""Shared feature-preparation helpers for the model-based families.

Clustering, dimensionality reduction, and supervised learning all need to turn
the stored table into a numeric, model-ready matrix. Doing that consistently —
same column selection, same encoding, same imputation — is what keeps results
comparable across families, so it lives here rather than being re-derived in each
module.

Column *classification* is never re-decided here; it is delegated to
validation.dtypes (the single source of truth). This module only decides how a
classified column is fed to scikit-learn.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .validation.dtypes import classify_column

# Column types (from validation.dtypes) that carry modelling signal and how they
# should be treated. Identifiers and datetimes are excluded from feature matrices.
_NUMERIC_TYPES = {"continuous"}
_CATEGORICAL_TYPES = {"categorical_nominal", "categorical_ordinal"}


def get_frame(store: Any) -> pd.DataFrame:
    """Return the full table in stable (_ti_row) order as a pandas DataFrame."""
    return store.get_frame()


def feature_columns(
    store: Any,
    exclude: tuple[str, ...] = (),
) -> tuple[list[str], list[str]]:
    """Split the table's columns into (numeric, categorical) feature lists.

    Identifier and datetime columns are dropped — they are not features. Any
    names in ``exclude`` (e.g. the supervised target, or a cluster-label column)
    are dropped too.

    Args:
        store: The Store instance.
        exclude: Column names to omit from both lists.

    Returns:
        (numeric_columns, categorical_columns).
    """
    # Derived annotations (outlier flags, cluster labels, predictions) are never
    # features — drop them alongside the caller's explicit excludes so they can't
    # leak into a model. reduce_dimensions marks its components feature=True, so
    # those stay eligible.
    get_derived = getattr(store, "derived_columns", None)
    excluded = set(exclude) | (get_derived() if get_derived else set())

    numeric: list[str] = []
    categorical: list[str] = []
    for name in store._table.schema():
        if name in excluded:
            continue
        kind = classify_column(name, store)
        if kind in _NUMERIC_TYPES:
            numeric.append(name)
        elif kind in _CATEGORICAL_TYPES:
            categorical.append(name)
        # identifier / datetime → intentionally skipped
    return numeric, categorical


def build_preprocessor(
    numeric: list[str],
    categorical: list[str],
    *,
    scale: bool,
) -> ColumnTransformer:
    """Build a ColumnTransformer that imputes, (optionally) scales, and one-hot encodes.

    Args:
        numeric: Numeric (continuous) feature column names.
        categorical: Categorical feature column names.
        scale: Whether to standard-scale numeric columns. Distance-based methods
            (k-means, PCA) need this; tree ensembles do not.

    Returns:
        An unfitted ColumnTransformer.
    """
    numeric_steps: list[tuple[str, Any]] = [("impute", SimpleImputer(strategy="median"))]
    if scale:
        numeric_steps.append(("scale", StandardScaler()))
    numeric_pipe = Pipeline(numeric_steps)

    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        # Dense output: HistGradientBoosting and the manifold methods reject sparse.
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    transformers = []
    if numeric:
        transformers.append(("numeric", numeric_pipe, numeric))
    if categorical:
        transformers.append(("categorical", categorical_pipe, categorical))
    return ColumnTransformer(transformers, remainder="drop")


def numeric_matrix(
    store: Any,
    exclude: tuple[str, ...] = (),
    *,
    scale: bool = True,
) -> tuple[Any, pd.DataFrame, list[str]]:
    """Materialize a fully numeric feature matrix for distance-based methods.

    Used by clustering and dimensionality reduction. Numeric columns are scaled
    (by default) and categorical columns one-hot encoded.

    Args:
        store: The Store instance.
        exclude: Column names to omit (e.g. an existing cluster-label column).
        scale: Whether to standard-scale numeric columns.

    Returns:
        (X, frame, feature_names) where X is the transformed 2-D array in stable
        row order, frame is the source DataFrame, and feature_names are the
        original feature column names (pre-encoding).
    """
    frame = get_frame(store)
    numeric, categorical = feature_columns(store, exclude=exclude)
    if not numeric and not categorical:
        raise ValueError("No usable feature columns (all identifier/datetime).")
    pre = build_preprocessor(numeric, categorical, scale=scale)
    X = pre.fit_transform(frame)
    # Densify sparse one-hot output so downstream estimators that dislike sparse
    # input (e.g. some sklearn manifold methods) work uniformly.
    if hasattr(X, "toarray"):
        X = X.toarray()
    return X, frame, numeric + categorical
