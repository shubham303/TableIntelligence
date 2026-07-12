"""Causal effect estimation — "what actually moves the metric", not just correlation.

``causal_effect`` estimates the average effect of a ``treatment`` column on an
``outcome`` column, adjusting for confounders via the backdoor criterion, and then
runs a refutation test so the number comes with a credibility check.

Library: **DoWhy** (``CausalModel``: identify → estimate → refute), imported lazily
via the optional ``insights`` extra. DoWhy encodes the whole identify/estimate/refute
workflow; we only choose sensible defaults (all other usable columns as common causes)
and format the result.
"""
from __future__ import annotations

from typing import Any

from ..results import Result
from . import _prep


def causal_effect(
    store: Any,
    treatment: str,
    outcome: str,
    confounders: list[str] | None = None,
) -> Result:
    """Estimate the average causal effect of ``treatment`` on ``outcome``.

    Args:
        store: The Store/Table instance.
        treatment: The intervention column (binary or continuous).
        outcome: The numeric outcome column.
        confounders: Columns to adjust for. Defaults to every other usable feature
            column (a backdoor-adjustment starting point — refine per domain).

    Returns:
        Result with ``effect`` (point estimate), ``refutation`` (placebo/random-cause
        check), and the confounder set used.
    """
    try:
        from dowhy import CausalModel
    except ImportError as exc:  # pragma: no cover - optional extra
        raise ImportError(
            "causal_effect needs DoWhy. Install it with:  pip install 'tabular[insights]'."
        ) from exc

    frame = store.get_frame()
    for col in (treatment, outcome):
        if col not in frame.columns:
            raise ValueError(f"Column {col!r} not in table.")

    if confounders is None:
        numeric, categorical = _prep.feature_columns(store, exclude=(treatment, outcome))
        confounders = numeric + categorical
    else:
        missing = [c for c in confounders if c not in frame.columns]
        if missing:
            raise ValueError(f"Confounder columns not in table: {missing}")

    data = frame[[treatment, outcome, *confounders]].dropna()
    if data.empty:
        raise ValueError("No complete rows across treatment, outcome, and confounders.")

    model = CausalModel(
        data=data,
        treatment=treatment,
        outcome=outcome,
        common_causes=confounders or None,
    )
    identified = model.identify_effect(proceed_when_unidentifiable=True)
    estimate = model.estimate_effect(
        identified, method_name="backdoor.linear_regression"
    )
    effect = float(estimate.value)

    # Refutation: adding a random common cause should NOT move a real effect much.
    refutation: dict[str, Any]
    try:
        ref = model.refute_estimate(
            identified, estimate, method_name="random_common_cause"
        )
        refutation = {
            "method": "random_common_cause",
            "new_effect": float(ref.new_effect)
            if isinstance(ref.new_effect, (int, float))
            else None,
            "passed": abs((ref.new_effect or 0) - effect) < 0.5 * (abs(effect) + 1e-9)
            if isinstance(ref.new_effect, (int, float))
            else None,
        }
    except Exception as exc:  # refutation is best-effort, never fatal
        refutation = {"method": "random_common_cause", "error": str(exc)}

    return Result(
        method="dowhy_backdoor_linear_regression",
        summary=f"Estimated effect of {treatment!r} on {outcome!r}: {effect:.4g}",
        values={"effect": effect, "refutation": refutation},
        metadata={
            "treatment": treatment,
            "outcome": outcome,
            "confounders": confounders,
            "n_rows": int(len(data)),
            "estimand": "backdoor",
        },
    )
