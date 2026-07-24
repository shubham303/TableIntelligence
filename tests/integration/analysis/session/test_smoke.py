"""Smoke tests for Session — DB-backed importability and wiring.

The pure Result/import tests live in ``unit/shared/test_results.py``. These
tests exercise the real Session.load/profile/analyze_association pipeline.

Mirrors: src/tabint/analysis/session.py
"""
from tabint import Session, Result
from tests.conftest import FIXTURES_DIR


def test_session_importable():
    """Session class is accessible from the top-level package."""
    assert Session is not None


def test_session_load_returns_session():
    """Session.load returns a wired Session backed by a store."""
    s = Session.load(str(FIXTURES_DIR / "customers.csv"))
    assert isinstance(s, Session)
    assert s._store is not None


def test_session_profile_runs():
    """Session().profile returns a Result over the loaded table."""
    s = Session.load(str(FIXTURES_DIR / "customers.csv"))
    result = s.profile()
    assert isinstance(result, Result)
    assert "age" in result.values


def test_session_analyze_association_runs():
    """Session().analyze_association returns a Result with a chosen method."""
    s = Session.load(str(FIXTURES_DIR / "customers.csv"))
    result = s.analyze_association("age", "total_spend")
    assert isinstance(result, Result)
    assert result.method in {"pearson", "spearman"}
