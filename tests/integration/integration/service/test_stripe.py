"""Integration tests for the Stripe connector via the MCP connect_stripe tool.

These spin up a real Session (DuckDB + filesystem) with only the Stripe HTTP
call mocked. The pure normalization/pagination contract tests live in
``unit/integration/service/test_stripe.py``.

Mirrors: src/tabint/analysis/tools.py:connect_stripe (exercises the real
connect → fetch → Session.load pipeline).
"""
from __future__ import annotations

import pytest

from tabint.analysis import tools as mcp_server
from tabint.integration.service import stripe as stripe_conn


# ── canned Stripe objects (mirrors the unit file) ─────────────────────────
CHARGE = {
    "id": "ch_1", "created": 1700000000, "amount": 2500, "currency": "usd",
    "customer": "cus_1", "status": "succeeded", "refunded": False, "description": "Order",
}
CUSTOMER = {
    "id": "cus_1", "created": 1699000000, "email": "a@b.com",
    "address": {"country": "US"}, "delinquent": False,
}
SUB = {
    "id": "sub_1", "customer": "cus_1", "status": "active", "created": 1699000000,
    "current_period_end": 1701000000, "canceled_at": None,
    "plan": {"amount": 999, "interval": "month"},
}
INVOICE = {
    "id": "in_1", "customer": "cus_1", "created": 1700000000,
    "amount_paid": 999, "amount_due": 0, "status": "paid",
}


@pytest.fixture()
def mocked_stripe(monkeypatch):
    """Stub Stripe HTTP with one canned page per resource."""
    def http(url, key):
        resource = url.split("/v1/")[1].split("?")[0]
        page = {
            "charges": [CHARGE], "customers": [CUSTOMER],
            "subscriptions": [SUB], "invoices": [INVOICE],
        }.get(resource, [])
        return {"data": page, "has_more": False}
    monkeypatch.setattr(stripe_conn, "_http_get", http)


# ── no role gating; only the Stripe-credential check ────────────────────────
def test_connect_stripe_needs_credentials(monkeypatch):
    # The MCP no longer role-gates connect_stripe; without a Stripe key it
    # surfaces no_credentials (the provider→machine fetch needs a key).
    # (Env was cleared by the unit conftest; we set it back for the negative
    #  case here explicitly.)
    monkeypatch.setenv("STRIPE_API_KEY", "")  # ensure empty even if CI sets it
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    monkeypatch.delenv("TABINT_STRIPE_KEY", raising=False)
    out = mcp_server.connect_stripe()
    assert out["error"] == "no_credentials"


def test_connect_stripe_creates_session(monkeypatch, tmp_path, mocked_stripe):
    from tabint.shared import server
    # The autouse _isolate_sessions fixture already redirects server._BASE to
    # tmp_path; reaffirm explicitly so this test is self-describing.
    monkeypatch.setattr(server, "_BASE", str(tmp_path))
    monkeypatch.setenv("STRIPE_API_KEY", "sk_test_x")
    out = mcp_server.connect_stripe(limit=100)
    assert "session_key" in out
    assert set(out["tables"]) >= {"payments", "customers", "subscriptions", "invoices"}
    assert out["row_counts"]["payments"] == 1
    assert "Stripe" in out["playbook"]
