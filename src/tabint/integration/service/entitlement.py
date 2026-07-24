"""Entitlement / role lookup for the Table Intelligence MCP server.

The MCP server is free to use and imposes NO client-side gating: every tool
runs locally regardless of subscription. This module exists only to let the
``account_status`` tool report the linked account's tier (free/pro) — the
authoritative gating for paid surfaces (persisting outreach/reports to the
dashboard) is enforced server-side by the API.

Two roles: ``free`` and ``pro``. The platform derives the role from the
better-auth-razorpay subscription table (active or within-trial => pro).

Design rules:
  * **Fails open to the free role.** Any network/config error => ``free``. The
    server must never crash because the control plane was unreachable.
  * **Stdlib only** (``urllib``) — no new runtime dependency.
  * **Cached** with a periodic re-check so we don't hit the network per call.

Env:
  ``TABINT_API_KEY``            the user's key (absent => free role)
  ``TABINT_CONTROL_PLANE_URL``  base URL of the control plane
                                (default: https://shubhamrandive.com)

Wire contract with the platform (POST /api/validate-key):
  request:  {"api_key": "ti_..."}            # key in the body, OR
            header  x-api-key: ti_...        # the same key in the header
  response: {"role": "free" | "pro", "trial_until": "<iso>" | null}
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

FREE = "free"
PRO = "pro"
_ROLES = {FREE, PRO}

_DEFAULT_CONTROL_PLANE = "https://shubhamrandive.com"
_RECHECK_SECONDS = 6 * 60 * 60  # re-validate at most every 6h
_TIMEOUT = 6  # network timeout (s); short so startup never hangs

# in-process cache: (role, checked_at_monotonic)
_cache: tuple[str, float] | None = None


def _control_plane_url() -> str:
    return (os.environ.get("TABINT_CONTROL_PLANE_URL") or _DEFAULT_CONTROL_PLANE).rstrip("/")


def _validate_remote(api_key: str) -> str:
    """Call the control plane; return a role string ('free' or 'pro').

    Raises on any failure so the caller can fail open.
    """
    url = f"{_control_plane_url()}/api/validate-key"
    payload = json.dumps({"api_key": api_key}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "x-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    role = str(body.get("role", FREE)).lower()
    return role if role in _ROLES else FREE


def role(force: bool = False) -> str:
    """Current role ('free' or 'pro'), cached with a periodic re-check.

    Fails open to FREE on missing key or any error. Pass ``force=True`` to
    bypass the cache (used by an explicit refresh).
    """
    global _cache
    now = time.monotonic()
    if not force and _cache is not None and (now - _cache[1]) < _RECHECK_SECONDS:
        return _cache[0]

    api_key = os.environ.get("TABINT_API_KEY", "").strip()
    if not api_key:
        _cache = (FREE, now)
        return FREE
    try:
        resolved = _validate_remote(api_key)
    except Exception:  # noqa: BLE001 - fail-open is the whole point; never raise
        # Keep a previous good role if we have one, else fall open to free.
        resolved = _cache[0] if _cache is not None else FREE
    _cache = (resolved, now)
    return resolved


def is_pro() -> bool:
    """True if the linked account is on the Pro tier (informational only)."""
    return role() == PRO


def status() -> dict:
    """Human-facing entitlement summary (for the ``account_status`` tool)."""
    r = role()
    return {
        "role": r,
        "pro_features_unlocked": r == PRO,
        "control_plane": _control_plane_url(),
        "note": (
            "The MCP server is free to use. Paid features (cloud artifact "
            "storage, dashboard sync) are enforced by the API; subscribe at "
            "https://shubhamrandive.com to unlock them."
            if r != PRO
            else "Pro is active — dashboard sync and artifact storage are unlocked."
        ),
    }
