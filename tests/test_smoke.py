"""Smoke tests: verify the package is importable and skeletons are wired correctly."""
import pytest
import tabint
from tabint import Session, Result


def test_import():
    """Package imports without errors."""
    assert tabint is not None


def test_session_importable():
    """Session class is accessible from the top-level package."""
    assert Session is not None


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


def test_session_load_returns_session():
    """Session.load returns a wired Session backed by a store."""
    s = Session.load("tests/fixtures/customers.csv")
    assert isinstance(s, Session)
    assert s._store is not None


def test_session_profile_runs():
    """Session().profile returns a Result over the loaded table."""
    s = Session.load("tests/fixtures/customers.csv")
    result = s.profile()
    assert isinstance(result, Result)
    assert "age" in result.values


def test_session_analyze_association_runs():
    """Session().analyze_association returns a Result with a chosen method."""
    s = Session.load("tests/fixtures/customers.csv")
    result = s.analyze_association("age", "total_spend")
    assert isinstance(result, Result)
    assert result.method in {"pearson", "spearman"}


def test_version():
    """Package exposes __version__."""
    assert tabint.__version__ == "0.1.0"
