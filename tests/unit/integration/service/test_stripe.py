"""Unit tests for the Stripe connector normalization contract (mocked HTTP).

Only ``_http_get`` is stubbed (via ``stub_http_get``); everything else — the
real ``StripeConnector`` and the ``conform()`` contract — runs unmodified. Tests
that spin up a real Session (``connect_stripe``) live in
``integration/integration/service/test_stripe.py``.

Mirrors: src/tabint/integration/service/stripe.py, schemas/stripe.py
"""
from __future__ import annotations

import pandas as pd

from tabint.integration.schemas import stripe as contract
from tabint.integration.service.base import get_connector
from tabint.integration.service import stripe as stripe_conn


# ── canned Stripe objects ─────────────────────────────────────────────────
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


# ── contract ──────────────────────────────────────────────────────────────
def test_conform_enforces_schema():
    df = pd.DataFrame([{"id": "x", "amount": 1.0, "junk": 9}])
    out = contract.conform(df, "payments")
    assert list(out.columns) == list(contract.SCHEMAS["payments"])   # exact + ordered
    assert "junk" not in out.columns
    assert pd.api.types.is_datetime64_any_dtype(out["created_at"])   # filled + typed


# ── normalization (mocked single-page HTTP) ───────────────────────────────
def test_fetch_normalizes_to_canonical(monkeypatch, stub_http_get):
    monkeypatch.setattr(
        stripe_conn, "_http_get",
        stub_http_get({
            "charges": [CHARGE], "customers": [CUSTOMER],
            "subscriptions": [SUB], "invoices": [INVOICE],
        }),
    )
    tables = get_connector("stripe").fetch("sk_test_x", limit=100)
    assert set(tables) == {"payments", "customers", "subscriptions", "invoices"}

    pay = tables["payments"]
    assert list(pay.columns) == list(contract.SCHEMAS["payments"])
    assert pay.loc[0, "amount"] == 25.0                # cents → dollars
    assert pay.loc[0, "customer_id"] == "cus_1"        # customer id extracted
    assert pd.api.types.is_datetime64_any_dtype(pay["created_at"])

    assert tables["subscriptions"].loc[0, "plan_amount"] == 9.99
    assert tables["subscriptions"].loc[0, "interval"] == "month"
    assert tables["invoices"].loc[0, "amount_paid"] == 9.99
    assert tables["customers"].loc[0, "country"] == "US"


# ── pagination (mocked multi-page HTTP) ───────────────────────────────────
def test_list_paginates(monkeypatch):
    pages = [
        {"data": [{"id": "ch_1"}, {"id": "ch_2"}], "has_more": True},
        {"data": [{"id": "ch_3"}], "has_more": False},
    ]
    seq = {"i": 0}

    def http(url, key):
        p = pages[min(seq["i"], len(pages) - 1)]
        seq["i"] += 1
        return p

    monkeypatch.setattr(stripe_conn, "_http_get", http)
    assert [c["id"] for c in stripe_conn._list("charges", "k", 100)] == ["ch_1", "ch_2", "ch_3"]


def test_list_respects_limit(monkeypatch):
    monkeypatch.setattr(
        stripe_conn, "_http_get",
        lambda url, key: {"data": [{"id": "a"}, {"id": "b"}], "has_more": True},
    )
    assert len(stripe_conn._list("charges", "k", 2)) == 2
