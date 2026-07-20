"""Tests for the honesty seam — trust envelope, decline-to-answer, retrofits."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tabint import honesty
from tabint._serialize import result_dict
from tabint.honesty import TrustLevel
from tabint.results import Result


class FakeStore:
    def __init__(self, df):
        self._df = df

    def get_frame(self):
        return self._df


# ── the module ────────────────────────────────────────────────────────────
def test_from_sample_size_levels():
    assert honesty.from_sample_size(5).level == TrustLevel.LOW
    assert honesty.from_sample_size(50).level == TrustLevel.MODERATE
    assert honesty.from_sample_size(500).level == TrustLevel.HIGH


def test_decline_sets_fields():
    t = honesty.decline("not enough data")
    assert t.declined is True
    assert t.level == TrustLevel.NONE
    assert t.decline_reason == "not enough data"


def test_combine_most_cautious_wins_and_dedupes():
    a = honesty.Trust(level=TrustLevel.HIGH, caveats=["x"])
    b = honesty.Trust(level=TrustLevel.LOW, caveats=["x", "y"])
    c = honesty.combine(a, b)
    assert c.level == TrustLevel.LOW
    assert c.caveats == ["x", "y"]


def test_combine_decline_dominates():
    a = honesty.Trust(level=TrustLevel.HIGH)
    b = honesty.decline("bad")
    assert honesty.combine(a, b).declined is True


# ── uniform envelope on every result ──────────────────────────────────────
def test_result_dict_defaults_to_unassessed():
    d = result_dict(Result(method="m", summary="s"))
    assert d["trust"]["level"] == "unassessed"
    assert d["declined"] is False


def test_result_dict_surfaces_decline():
    r = Result(method="m", summary="s", trust=honesty.decline("no counterfactual"))
    d = result_dict(r)
    assert d["declined"] is True
    assert d["trust"]["level"] == "none"
    assert d["trust"]["decline_reason"] == "no counterfactual"


# ── retrofit: compare_periods ─────────────────────────────────────────────
def test_compare_periods_attaches_low_trust_on_small_sample():
    from tabint.analytics.compare import compare_periods

    df = pd.DataFrame(
        {
            "t": pd.date_range("2024-01-01", periods=20, freq="D"),
            "v": np.arange(20, dtype=float),
        }
    )
    res = compare_periods(FakeStore(df), "t", "v")
    assert res.trust is not None
    assert res.trust.level == TrustLevel.LOW           # 10 per window < 30
    assert res.trust.declined is False
    assert any("before/after" in c.lower() for c in res.trust.caveats)


# ── retrofit: causal_effect declines (no DoWhy needed — refuses first) ─────
def test_causal_declines_on_too_few_rows():
    from tabint.analytics.causal import causal_effect

    df = pd.DataFrame({"tx": [0, 1] * 5, "y": np.arange(10.0), "c": np.arange(10.0)})
    res = causal_effect(FakeStore(df), treatment="tx", outcome="y", confounders=["c"])
    assert res.method == "causal_effect_declined"
    assert res.trust.declined is True
    assert res.values == {}                            # no meaningless number emitted


def test_causal_declines_on_no_treatment_variation():
    from tabint.analytics.causal import causal_effect

    df = pd.DataFrame({"tx": [1] * 60, "y": np.arange(60.0), "c": np.arange(60.0)})
    res = causal_effect(FakeStore(df), treatment="tx", outcome="y", confounders=["c"])
    assert res.trust.declined is True
    assert "counterfactual" in res.trust.decline_reason
