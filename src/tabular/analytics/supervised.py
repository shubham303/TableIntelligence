"""Supervised learning family.

Planned functions: train_classifier, train_regressor, evaluate.
Planned class: TrainedModel (a callable artifact, not a Result).
Libraries (planned, not yet imported): scikit-learn, xgboost, lightgbm;
autogluon for the slow-lane path.
"""
from __future__ import annotations

from typing import Any

# planned: from sklearn.pipeline import Pipeline
# planned: from sklearn.model_selection import train_test_split
# planned: import xgboost as xgb


class TrainedModel:
    """A callable artifact returned by train_classifier and train_regressor.

    Bundles fitted preprocessing (encoders, scaler, feature list) alongside the
    fitted model so new rows are transformed identically at predict time. This
    prevents train/serve skew.

    Unlike Result, TrainedModel is a live object with behavior, not an inert
    data container.
    """

    def __init__(self) -> None:
        self._pipeline: Any = None
        self._feature_names: list[str] = []
        self._target: str = ""

    def predict(self, X: Any) -> Any:
        """Generate predictions for new rows.

        Args:
            X: A pandas DataFrame or dict of feature values.

        Returns:
            Array of predicted values or class labels.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def predict_proba(self, X: Any) -> Any:
        """Generate class probability estimates (classifiers only).

        Args:
            X: A pandas DataFrame or dict of feature values.

        Returns:
            Array of shape (n_samples, n_classes) with class probabilities.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")


def train_classifier(store: Any, target: str) -> TrainedModel:
    """Train a classification model on the loaded table (fast lane).

    Handles categorical encoding, missing values, and a proper train/test split.
    Default algorithm: gradient-boosted trees (xgboost or lightgbm).

    Args:
        store: The Store instance holding the table.
        target: Name of the binary or multiclass target column.

    Returns:
        TrainedModel with bundled preprocessing and .predict() / .predict_proba().
    """
    raise NotImplementedError("planned: see docs/roadmap.md")


def train_regressor(store: Any, target: str) -> TrainedModel:
    """Train a regression model on the loaded table (fast lane).

    Handles categorical encoding, missing values, and a proper train/test split.
    Default algorithm: gradient-boosted trees (xgboost or lightgbm).

    Args:
        store: The Store instance holding the table.
        target: Name of the continuous target column.

    Returns:
        TrainedModel with bundled preprocessing and .predict().
    """
    raise NotImplementedError("planned: see docs/roadmap.md")


def evaluate(store: Any, model: TrainedModel) -> Any:
    """Evaluate a trained model with a full metric set.

    For classifiers: accuracy, precision, recall, F1, ROC-AUC, confusion matrix.
    For regressors: MAE, RMSE, R².

    Args:
        store: The Store instance (provides the held-out test split).
        model: A TrainedModel returned by train_classifier or train_regressor.

    Returns:
        Result with metric values, confusion matrix (classifiers), and eval params.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
