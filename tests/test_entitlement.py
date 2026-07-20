"""Tests for the entitlement/gating layer — fail-open, caching, paid gating."""
from __future__ import annotations

import json

import pytest

from tabint import entitlement


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    """Clear the module cache and env before each test."""
    entitlement._cache = None
    monkeypatch.delenv("TABINT_API_KEY", raising=False)
    monkeypatch.delenv("TABINT_CONTROL_PLANE_URL", raising=False)
    monkeypatch.delenv("TABINT_CONTROL_DB", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    yield
    entitlement._cache = None


def test_no_key_is_free():
    assert entitlement.tier() == entitlement.FREE
    assert entitlement.is_paid() is False


def test_network_error_fails_open_to_free(monkeypatch):
    monkeypatch.setenv("TABINT_API_KEY", "k_test")

    def _boom(_key):
        raise OSError("network down")

    monkeypatch.setattr(entitlement, "_validate_remote", _boom)
    assert entitlement.tier(force=True) == entitlement.FREE
    assert entitlement.is_paid() is False


@pytest.mark.parametrize(
    "resolved,expected_paid",
    [("paid", True), ("trial", True), ("free", False), ("expired", False)],
)
def test_remote_tier_drives_entitlement(monkeypatch, resolved, expected_paid):
    monkeypatch.setenv("TABINT_API_KEY", "k_test")
    monkeypatch.setattr(entitlement, "_validate_remote", lambda _k: resolved)
    assert entitlement.tier(force=True) == resolved
    assert entitlement.is_paid() is expected_paid


def test_cache_avoids_repeat_calls(monkeypatch):
    monkeypatch.setenv("TABINT_API_KEY", "k_test")
    calls = {"n": 0}

    def _count(_key):
        calls["n"] += 1
        return "paid"

    monkeypatch.setattr(entitlement, "_validate_remote", _count)
    assert entitlement.tier(force=True) == "paid"  # 1 call
    assert entitlement.tier() == "paid"            # cached, no call
    assert entitlement.tier() == "paid"            # cached, no call
    assert calls["n"] == 1


def test_requires_paid_blocks_when_free(monkeypatch):
    monkeypatch.setattr(entitlement, "is_paid", lambda: False)
    monkeypatch.setattr(entitlement, "tier", lambda force=False: "free")

    @entitlement.requires_paid
    def fetch_shopify():
        return {"ok": True, "rows": 10}

    out = fetch_shopify()
    assert out["ok"] is False
    assert out["error"] == "paid_feature"
    assert "shubhamrandive.com" in out["message"]


def test_requires_paid_runs_when_entitled(monkeypatch):
    monkeypatch.setattr(entitlement, "is_paid", lambda: True)

    @entitlement.requires_paid
    def fetch_shopify():
        return {"ok": True, "rows": 10}

    assert fetch_shopify() == {"ok": True, "rows": 10}


def test_local_mode_resolves_via_service(monkeypatch, tmp_path):
    """End-to-end: mint a paid key in a local DuckDB control plane, then the
    entitlement client (local mode) resolves it to paid."""
    from tabint_control import create_provider
    from tabint_control.services import AdminService

    db_path = str(tmp_path / "control.duckdb")
    provider = create_provider(db_path)
    provider.init_schema()
    key, _ = AdminService(provider.users, provider.api_keys).mint_key("dev@x.com", "paid")
    provider.close()

    monkeypatch.setenv("TABINT_CONTROL_DB", db_path)
    monkeypatch.setenv("TABINT_API_KEY", key)
    assert entitlement.tier(force=True) == "paid"
    assert entitlement.is_paid() is True


def test_validate_remote_parses_tier(monkeypatch):
    monkeypatch.setenv("TABINT_CONTROL_PLANE_URL", "https://api.example.com")

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"tier": "paid", "expires_at": None}).encode()

    monkeypatch.setattr(entitlement.urllib.request, "urlopen", lambda *a, **k: _Resp())
    assert entitlement._validate_remote("k_test") == "paid"
