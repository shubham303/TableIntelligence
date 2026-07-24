"""Tests for the entitlement/role lookup — fail-open, caching, role resolution.

The MCP server does no client-side gating; these cover the informational role
lookup that ``account_status`` relies on. ``_validate_remote`` is either
monkeypatched directly or exercised with a stubbed ``urlopen`` — no real
network or DuckDB is involved.

Mirrors: src/tabint/integration/service/entitlement.py
"""
from __future__ import annotations

import json

import pytest

from tabint.integration.service import entitlement


@pytest.fixture(autouse=True)
def _reset_cache(monkeypatch):
    """Clear the module cache before each test (env is already cleared by the
    unit conftest's ``_clear_network_env``)."""
    entitlement._cache = None
    yield
    entitlement._cache = None


def test_no_key_is_free():
    assert entitlement.role() == entitlement.FREE
    assert entitlement.is_pro() is False


def test_network_error_fails_open_to_free(monkeypatch):
    monkeypatch.setenv("TABINT_API_KEY", "k_test")

    def _boom(_key):
        raise OSError("network down")

    monkeypatch.setattr(entitlement, "_validate_remote", _boom)
    assert entitlement.role(force=True) == entitlement.FREE
    assert entitlement.is_pro() is False


@pytest.mark.parametrize(
    "resolved,expected_pro",
    [("pro", True), ("free", False)],
)
def test_remote_role_drives_entitlement(monkeypatch, resolved, expected_pro):
    monkeypatch.setenv("TABINT_API_KEY", "k_test")
    monkeypatch.setattr(entitlement, "_validate_remote", lambda _k: resolved)
    assert entitlement.role(force=True) == resolved
    assert entitlement.is_pro() is expected_pro


def test_unknown_role_coerces_to_free(monkeypatch):
    """The wire contract is free|pro; anything else (incl. legacy 'paid' or
    'premium') is coerced to free client-side rather than granting access.

    Exercises the coercion inside _validate_remote itself (not role()), so we
    stub urlopen and let the real parser run.
    """
    monkeypatch.setenv("TABINT_API_KEY", "k_test")

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"role": "premium"}).encode()

    monkeypatch.setattr(entitlement.urllib.request, "urlopen", lambda *a, **k: _Resp())
    assert entitlement._validate_remote("k_test") == entitlement.FREE


def test_cache_avoids_repeat_calls(monkeypatch):
    monkeypatch.setenv("TABINT_API_KEY", "k_test")
    calls = {"n": 0}

    def _count(_key):
        calls["n"] += 1
        return "pro"

    monkeypatch.setattr(entitlement, "_validate_remote", _count)
    assert entitlement.role(force=True) == "pro"  # 1 call
    assert entitlement.role() == "pro"            # cached, no call
    assert entitlement.role() == "pro"            # cached, no call
    assert calls["n"] == 1


def test_status_reports_role_and_note(monkeypatch):
    """status() feeds account_status: it reports the role and a human note,
    regardless of tier (there is no client-side gating to assert on)."""
    monkeypatch.setattr(entitlement, "role", lambda force=False: "free")
    s = entitlement.status()
    assert s["role"] == "free"
    assert s["pro_features_unlocked"] is False
    assert "shubhamrandive.com" in s["note"]

    monkeypatch.setattr(entitlement, "role", lambda force=False: "pro")
    s = entitlement.status()
    assert s["role"] == "pro"
    assert s["pro_features_unlocked"] is True


def test_validate_remote_parses_role(monkeypatch):
    """The new wire contract returns {role: ...} (was {tier: ...})."""
    monkeypatch.setenv("TABINT_CONTROL_PLANE_URL", "https://api.example.com")

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"role": "pro", "trial_until": None}).encode()

    monkeypatch.setattr(entitlement.urllib.request, "urlopen", lambda *a, **k: _Resp())
    assert entitlement._validate_remote("k_test") == "pro"
