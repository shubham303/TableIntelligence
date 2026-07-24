"""Tests for the honesty seam — trust envelope and decline-to-answer.

Pure trust-logic tests only. Tests that exercise an algorithm (compare_periods,
causal_effect) through the honesty seam live next to those algorithms under
``unit/analysis/service/algorithms/``.

Mirrors: src/tabint/shared/honesty.py
"""
from tabint.shared import honesty
from tabint.shared.serialize import result_dict
from tabint.shared.honesty import TrustLevel
from tabint.shared.results import Result


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
