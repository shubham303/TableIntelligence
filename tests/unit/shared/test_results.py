"""Tests for the Result model — construction and repr.

The DB-backed smoke tests (Session.load/profile/analyze_association) live in
integration/analysis/session/test_smoke.py.

Mirrors: src/tabint/shared/results.py
"""
import tabint
from tabint import Result


def test_import():
    """Package imports without errors."""
    assert tabint is not None


def test_result_importable():
    """Result class is accessible from the top-level package."""
    assert Result is not None


def test_result_instantiation():
    """Result can be instantiated with just a method name (all other fields optional)."""
    r = Result(method="test_method")
    assert r.method == "test_method"
    assert r.summary == ""
    assert r.values == {}
    assert r.metadata == {}
    assert r.artifact is None


def test_result_repr():
    """Result __repr__ is readable."""
    r = Result(method="pearson", summary="strong positive correlation")
    assert "pearson" in repr(r)
    assert "strong positive correlation" in repr(r)


def test_version():
    """Package exposes __version__."""
    assert tabint.__version__ == "0.1.1"
