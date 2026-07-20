"""Stripe connector — pulls charges, customers, subscriptions, invoices and
normalizes them to the canonical contract.

Talks to the Stripe REST API directly from this machine with a secret key the user
supplies (a test-mode ``sk_test_...`` is perfect to start). No SDK dependency — plain
``urllib`` + cursor pagination. Nothing is sent anywhere except Stripe.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

import pandas as pd

from . import contract
from .base import Connector, register

_BASE = "https://api.stripe.com/v1"
_TIMEOUT = 30
_PAGE = 100


def _http_get(url: str, key: str) -> dict:
    """Single GET against Stripe. Isolated so tests can monkeypatch it."""
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _list(resource: str, key: str, limit: int, params: dict | None = None) -> list[dict]:
    """Cursor-paginate a Stripe list endpoint up to ``limit`` objects."""
    out: list[dict] = []
    after: str | None = None
    while len(out) < limit:
        query = {"limit": min(_PAGE, limit - len(out))}
        if after:
            query["starting_after"] = after
        if params:
            query.update(params)
        page = _http_get(f"{_BASE}/{resource}?{urllib.parse.urlencode(query)}", key)
        data = page.get("data", [])
        if not data:
            break
        out.extend(data)
        if not page.get("has_more"):
            break
        after = data[-1]["id"]
    return out[:limit]


def _epoch(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, unit="s", utc=True, errors="coerce")


def _cust(obj) -> str | None:
    """Stripe returns customer as an id string or an expanded object."""
    if isinstance(obj, dict):
        return obj.get("id")
    return obj


def _payments_df(charges: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {
                "id": c.get("id"),
                "created_at": c.get("created"),
                "amount": (c.get("amount") or 0) / 100.0,
                "currency": c.get("currency"),
                "customer_id": _cust(c.get("customer")),
                "status": c.get("status"),
                "refunded": c.get("refunded"),
                "description": c.get("description"),
            }
            for c in charges
        ]
    )
    if not df.empty:
        df["created_at"] = _epoch(df["created_at"])
    return contract.conform(df, "payments")


def _customers_df(customers: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {
                "id": c.get("id"),
                "created_at": c.get("created"),
                "email": c.get("email"),
                "country": (c.get("address") or {}).get("country"),
                "delinquent": c.get("delinquent"),
            }
            for c in customers
        ]
    )
    if not df.empty:
        df["created_at"] = _epoch(df["created_at"])
    return contract.conform(df, "customers")


def _subscriptions_df(subs: list[dict]) -> pd.DataFrame:
    def _plan_amount(s):
        plan = s.get("plan") or {}
        amt = plan.get("amount")
        return (amt or 0) / 100.0 if amt is not None else None

    def _interval(s):
        return (s.get("plan") or {}).get("interval")

    df = pd.DataFrame(
        [
            {
                "id": s.get("id"),
                "customer_id": _cust(s.get("customer")),
                "status": s.get("status"),
                "created_at": s.get("created"),
                "current_period_end": s.get("current_period_end"),
                "canceled_at": s.get("canceled_at"),
                "plan_amount": _plan_amount(s),
                "interval": _interval(s),
            }
            for s in subs
        ]
    )
    if not df.empty:
        for col in ("created_at", "current_period_end", "canceled_at"):
            df[col] = _epoch(df[col])
    return contract.conform(df, "subscriptions")


def _invoices_df(invoices: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {
                "id": i.get("id"),
                "customer_id": _cust(i.get("customer")),
                "created_at": i.get("created"),
                "amount_paid": (i.get("amount_paid") or 0) / 100.0,
                "amount_due": (i.get("amount_due") or 0) / 100.0,
                "status": i.get("status"),
            }
            for i in invoices
        ]
    )
    if not df.empty:
        df["created_at"] = _epoch(df["created_at"])
    return contract.conform(df, "invoices")


_PLATFORM_PROMPT = """You've connected a Stripe account. Canonical tables (all local to this
machine): payments, customers, subscriptions, invoices — amounts are in major currency units,
timestamps are UTC.

Good analyses to offer:
- Revenue trend / MoM change: compare_periods on payments (created_at, amount), or forecast on
  daily revenue.
- Customer value & segments: rfm on payments (customer_id, created_at, amount).
- Retention / churn: retention_cohorts on payments (customer_id, created_at); for subscriptions,
  look at status and canceled_at.
- Refund / failure rates: group_aggregate payments by status/refunded.
Join on customer_id ↔ customers.id / subscriptions.customer_id.

Always report the trust level and any caveats the tools return, and if a tool declines, tell the
user why rather than inventing a number. Note: test-mode keys return only test data."""


@register
class StripeConnector(Connector):
    name = "stripe"
    entities = ("payments", "customers", "subscriptions", "invoices")
    platform_prompt = _PLATFORM_PROMPT

    def fetch(self, credential: str, *, limit: int = 1000, **opts) -> dict[str, pd.DataFrame]:
        if not credential:
            raise ValueError("A Stripe secret key is required (e.g. sk_test_...).")
        return {
            "payments": _payments_df(_list("charges", credential, limit)),
            "customers": _customers_df(_list("customers", credential, limit)),
            "subscriptions": _subscriptions_df(
                _list("subscriptions", credential, limit, {"status": "all"})
            ),
            "invoices": _invoices_df(_list("invoices", credential, limit)),
        }
