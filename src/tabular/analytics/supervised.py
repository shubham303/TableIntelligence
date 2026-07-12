"""Supervised learning family — two selectable backends.

train_classifier / train_regressor build a scikit-learn Pipeline (shared
preprocessing + an estimator), fit it on a proper train/test split, and return a
TrainedModel that bundles the fitted preprocessing so new rows are transformed
identically at predict time (no train/serve skew).

Backends (``backend=``):

* ``"gbt"`` (default) — sklearn-native HistGradientBoosting. No fragile system
  deps, strong default on tabular data, works on CPU at any size.
* ``"tabicl"`` — TabICL v2, a tabular *foundation model*. One forward pass through
  a pre-trained transformer (in-context learning, no per-task gradient training);
  often beats tuned trees out of the box on small/medium tables. Fully open,
  commercial use permitted. Requires the optional ``tabicl`` dependency and is
  GPU-recommended. This is the opt-in "power" lane — see
  ``.claude-artifacts/integrate_foundational_model.md``.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    root_mean_squared_error,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from ..results import Result
from ..validation.dtypes import classify_column
from . import _prep

_TEST_SIZE = 0.25
_RANDOM_STATE = 0

_DEFAULT_BACKEND = "gbt"
_BACKENDS = ("gbt", "tabicl")

# TabICL v2 operating envelope. Beyond these it degrades / errors; we refuse early
# with a clear message rather than let the foundation model fail deep in a forward
# pass. Sourced from the model's stated ceilings (~500k rows; wide feature counts
# trade off against rows).
_TABICL_MAX_ROWS = 500_000
_TABICL_MAX_FEATURES = 2_000


def _make_estimator(task: str, backend: str) -> Any:
    """Return an unfitted sklearn-compatible estimator for (task, backend)."""
    if backend == "gbt":
        return (
            HistGradientBoostingClassifier(random_state=_RANDOM_STATE)
            if task == "classification"
            else HistGradientBoostingRegressor(random_state=_RANDOM_STATE)
        )
    if backend == "tabicl":
        try:
            from tabicl import TabICLClassifier, TabICLRegressor
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ImportError(
                "backend='tabicl' needs the optional TabICL dependency. "
                "Install it with:  pip install 'tabular[tabicl]'  (or  pip install tabicl)."
            ) from exc
        return TabICLClassifier() if task == "classification" else TabICLRegressor()
    raise ValueError(f"Unknown backend {backend!r}; choose one of {_BACKENDS}.")


def _check_backend_limits(backend: str, n_rows: int, n_features: int) -> None:
    """Refuse early when a table exceeds a backend's operating envelope."""
    if backend != "tabicl":
        return
    if n_rows > _TABICL_MAX_ROWS:
        raise ValueError(
            f"backend='tabicl' supports up to ~{_TABICL_MAX_ROWS:,} rows; "
            f"table has {n_rows:,}. Use backend='gbt' for larger tables."
        )
    if n_features > _TABICL_MAX_FEATURES:
        raise ValueError(
            f"backend='tabicl' supports up to ~{_TABICL_MAX_FEATURES:,} features; "
            f"table has {n_features:,} (after encoding). Use backend='gbt' instead."
        )


class TrainedModel:
    """A callable artifact bundling fitted preprocessing + a fitted estimator.

    Unlike Result, this is a live object with behaviour. It also retains the
    held-out test split so evaluate() and permutation importance run on data the
    model never saw during training.
    """

    def __init__(
        self,
        pipeline: Pipeline,
        numeric_features: list[str],
        categorical_features: list[str],
        target: str,
        task: str,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        backend: str = _DEFAULT_BACKEND,
    ) -> None:
        self._pipeline = pipeline
        self._numeric_features = numeric_features
        self._categorical_features = categorical_features
        self._feature_names = numeric_features + categorical_features
        self._target = target
        self._task = task  # "classification" | "regression"
        self._backend = backend  # "gbt" | "tabicl"
        self._X_test = X_test
        self._y_test = y_test

    def predict(self, X: Any) -> np.ndarray:
        """Predict values / class labels for new rows.

        Args:
            X: A pandas DataFrame, or a dict / list of dicts of feature values.

        Returns:
            Array of predictions.
        """
        return self._pipeline.predict(self._as_frame(X))

    def predict_proba(self, X: Any) -> np.ndarray:
        """Predict class probabilities (classifiers only)."""
        if self._task != "classification":
            raise ValueError("predict_proba is only available for classifiers.")
        return self._pipeline.predict_proba(self._as_frame(X))

    def _as_frame(self, X: Any) -> pd.DataFrame:
        if isinstance(X, pd.DataFrame):
            frame = X
        elif isinstance(X, dict):
            frame = pd.DataFrame([X])
        else:
            frame = pd.DataFrame(list(X))
        # Keep only known features; the ColumnTransformer selects by name.
        missing = [c for c in self._feature_names if c not in frame.columns]
        if missing:
            raise ValueError(f"Missing feature columns at predict time: {missing}")
        return frame


def train_classifier(store: Any, target: str, backend: str = _DEFAULT_BACKEND) -> TrainedModel:
    """Train a classifier on the table.

    Args:
        store: The Store instance.
        target: Target column name.
        backend: ``"gbt"`` (default, gradient-boosted trees) or ``"tabicl"``
            (TabICL v2 foundation model — opt-in power lane).
    """
    return _train(store, target, task="classification", backend=backend)


def train_regressor(store: Any, target: str, backend: str = _DEFAULT_BACKEND) -> TrainedModel:
    """Train a regressor on the table.

    Args:
        store: The Store instance.
        target: Target column name.
        backend: ``"gbt"`` (default, gradient-boosted trees) or ``"tabicl"``
            (TabICL v2 foundation model — opt-in power lane).
    """
    return _train(store, target, task="regression", backend=backend)


def _train(store: Any, target: str, task: str, backend: str = _DEFAULT_BACKEND) -> TrainedModel:
    if backend not in _BACKENDS:
        raise ValueError(f"Unknown backend {backend!r}; choose one of {_BACKENDS}.")

    frame = store.get_frame()
    if target not in frame.columns:
        raise ValueError(f"Target column {target!r} not in table.")

    numeric, categorical = _prep.feature_columns(store, exclude=(target,))
    if not numeric and not categorical:
        raise ValueError("No usable feature columns to train on.")

    X = frame[numeric + categorical]
    y = frame[target]
    # Drop rows with a missing target for BOTH tasks: neither classifier nor
    # regressor can learn from (or, for the regressor, even accept) a NaN label.
    rows = y.notna()
    X, y = X[rows], y[rows]
    if y.empty:
        raise ValueError(f"Target column {target!r} has no non-null values to train on.")
    if task == "regression" and not pd.api.types.is_numeric_dtype(y):
        raise ValueError(f"train_regressor needs a numeric target; {target!r} is not numeric.")

    # Enforce the backend's operating envelope BEFORE importing/instantiating it,
    # so an oversized table fails fast rather than deep in the optional dependency.
    _check_backend_limits(backend, n_rows=len(X), n_features=len(numeric + categorical))

    # Neither trees nor TabICL need scaling; still impute + one-hot for uniform
    # handling and a fully numeric matrix the foundation model can consume.
    pre = _prep.build_preprocessor(numeric, categorical, scale=False)
    estimator = _make_estimator(task, backend)
    pipeline = Pipeline([("pre", pre), ("model", estimator)])

    stratify = y if (task == "classification" and y.value_counts().min() >= 2) else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=_TEST_SIZE, random_state=_RANDOM_STATE, stratify=stratify
    )
    pipeline.fit(X_train, y_train)

    return TrainedModel(
        pipeline=pipeline,
        numeric_features=numeric,
        categorical_features=categorical,
        target=target,
        task=task,
        X_test=X_test,
        y_test=y_test,
        backend=backend,
    )


def evaluate(store: Any, model: TrainedModel) -> Result:
    """Evaluate a trained model on its held-out test split.

    Classifiers: accuracy, precision, recall, F1, ROC-AUC, confusion matrix.
    Regressors: MAE, RMSE, R².

    Args:
        store: The Store instance (kept for signature symmetry; the held-out
            split lives on the model).
        model: A TrainedModel from train_classifier / train_regressor.

    Returns:
        Result with the metric set and evaluation parameters.
    """
    X_test, y_test = model._X_test, model._y_test
    y_pred = model.predict(X_test)

    if model._task == "classification":
        values: dict[str, Any] = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        }
        values["roc_auc"] = _safe_roc_auc(model, X_test, y_test)
        summary = f"accuracy={values['accuracy']:.3f}, f1={values['f1']:.3f}"
        method = "classification_metrics"
    else:
        values = {
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(root_mean_squared_error(y_test, y_pred)),
            "r2": float(r2_score(y_test, y_pred)),
        }
        summary = f"R²={values['r2']:.3f}, RMSE={values['rmse']:.3g}"
        method = "regression_metrics"

    return Result(
        method=method,
        summary=summary,
        values=values,
        metadata={
            "target": model._target,
            "task": model._task,
            "backend": getattr(model, "_backend", _DEFAULT_BACKEND),
            "n_test": int(len(y_test)),
        },
    )


def _safe_roc_auc(model: TrainedModel, X_test: pd.DataFrame, y_test: pd.Series) -> float | None:
    """ROC-AUC, handling binary vs multiclass; None if it can't be computed."""
    try:
        proba = model.predict_proba(X_test)
        classes = model._pipeline.named_steps["model"].classes_
        if len(classes) == 2:
            return float(roc_auc_score(y_test, proba[:, 1]))
        return float(roc_auc_score(y_test, proba, multi_class="ovr", average="weighted"))
    except Exception:
        return None
