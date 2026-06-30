"""Smoke tests: verify the package is importable and skeletons are wired correctly."""
import pytest
import tabular
from tabular import Session, Result


def test_import():
    """Package imports without errors."""
    assert tabular is not None


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


def test_session_load_raises():
    """Session.load raises NotImplementedError — skeleton is wired correctly."""
    with pytest.raises(NotImplementedError):
        Session.load("customers.csv")


def test_session_profile_raises():
    """Session().profile raises NotImplementedError."""
    s = Session()
    with pytest.raises(NotImplementedError):
        s.profile()


def test_session_analyze_association_raises():
    """Session().analyze_association raises NotImplementedError."""
    s = Session()
    with pytest.raises(NotImplementedError):
        s.analyze_association("col_a", "col_b")


def test_version():
    """Package exposes __version__."""
    assert tabular.__version__ == "0.0.0"
