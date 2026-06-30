"""Model interpretation family.

Planned functions: feature_importance, explain_prediction.
Libraries (planned, not yet imported): shap.
"""
from __future__ import annotations

from typing import Any

# planned: import shap


def feature_importance(model: Any) -> Any:
    """Compute feature importance for a trained model.

    Reports both gain-based importance (from the model's internal structure)
    and permutation importance (model-agnostic, computed on the test split).

    Args:
        model: A TrainedModel returned by train_classifier or train_regressor.

    Returns:
        Result with importance scores per feature, sorted descending.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")


def explain_prediction(model: Any, row: Any) -> Any:
    """Explain a single prediction using SHAP values.

    Args:
        model: A TrainedModel returned by train_classifier or train_regressor.
        row: A single row as a pandas Series or dict of feature values.

    Returns:
        Result with per-feature SHAP contributions and the base value.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
