"""Unit tests for causal_effect declines (no DoWhy needed — refuses first).

causal_effect declines on too-few-rows or no-treatment-variation before ever
importing DoWhy, so the DuckDB layer can be faked. Exercises the honesty seam.

Mirrors: src/tabint/analysis/service/algorithms/causal.py
"""
import numpy as np
import pandas as pd


def test_causal_declines_on_too_few_rows(fake_store):
    from tabint.analysis.service.algorithms.causal import causal_effect

    df = pd.DataFrame({"tx": [0, 1] * 5, "y": np.arange(10.0), "c": np.arange(10.0)})
    res = causal_effect(fake_store(df), treatment="tx", outcome="y", confounders=["c"])
    assert res.method == "causal_effect_declined"
    assert res.trust.declined is True
    assert res.values == {}                            # no meaningless number emitted


def test_causal_declines_on_no_treatment_variation(fake_store):
    from tabint.analysis.service.algorithms.causal import causal_effect

    df = pd.DataFrame({"tx": [1] * 60, "y": np.arange(60.0), "c": np.arange(60.0)})
    res = causal_effect(fake_store(df), treatment="tx", outcome="y", confounders=["c"])
    assert res.trust.declined is True
    assert "counterfactual" in res.trust.decline_reason
