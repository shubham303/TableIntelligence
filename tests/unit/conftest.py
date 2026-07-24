"""Unit-test conftest — fakes for everything a unit under test depends on.

Unit tests exercise one unit with all collaborators mocked or faked. The fakes
here are deliberately minimal: only the surface the algorithms actually use.
"""
from __future__ import annotations

import pandas as pd
import pytest


# ── FakeStore — the minimal store duck-type ────────────────────────────────
#
# Algorithm functions (compare_periods, causal_effect, …) take a `store` object
# and only ever call ``store.get_frame()``. This fake is the single place that
# contract is encoded; promoting it here lets every algorithm unit test share
# it instead of redefining a class.

class FakeStore:
    """Minimal stand-in for a Workspace/Table — just returns a DataFrame.

    Add methods here only when a unit test genuinely needs them; most algorithm
    units need nothing beyond ``get_frame()``.
    """

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def get_frame(self) -> pd.DataFrame:
        return self._df


@pytest.fixture
def fake_store():
    """Factory fixture: ``fake_store(df)`` -> a FakeStore wrapping `df`."""
    def _make(df: pd.DataFrame) -> FakeStore:
        return FakeStore(df)
    return _make


# ── stub HTTP — for connector units that isolate urllib ────────────────────

def _stub_http_get(mapping: dict):
    """Return a stub ``_http_get(url, key)`` yielding one page per resource.

    Each resource key (e.g. ``"charges"``) maps to a list of objects; the stub
    always reports ``has_more=False`` so pagination terminates after one page.
    Promoted from test_connectors_stripe.py's ``_single_page_http``.
    """
    def http(url, key):
        resource = url.split("/v1/")[1].split("?")[0]
        return {"data": mapping.get(resource, []), "has_more": False}
    return http


@pytest.fixture
def stub_http_get():
    """Factory fixture: ``stub_http_get({resource: [...]})`` -> a stub _http_get."""
    return _stub_http_get


# ── network safety — unit tests must never hit the wire ────────────────────

@pytest.fixture(autouse=True)
def _clear_network_env(monkeypatch):
    """Strip credentials so a misconfigured unit test cannot make a real call."""
    for var in ("TABINT_API_KEY", "TABINT_STRIPE_KEY", "STRIPE_API_KEY"):
        monkeypatch.delenv(var, raising=False)
