"""Entitlement / role gating for the Table Intelligence MCP server.

Local-first pricing model: all analytics tools are free forever; connectors
and cloud artifact storage are Pro. This module answers one question — *is
this install entitled to Pro features?* — by validating the user's API key
against the control plane (the shubham-site platform).

Two roles: ``free`` and ``pro``. The platform derives the role from the
better-auth-razorpay subscription table (active or within-trial => pro).

Design rules:
  * **Fails open to the free role.** Any network/config error => ``free``. The
    server must never crash or block core analytics because auth was unreachable.
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
    """True if the install is entitled to Pro features."""
    return role() == PRO


def status() -> dict:
    """Human-facing entitlement summary (for the ``account_status`` tool)."""
    r = role()
    return {
        "role": r,
        "pro_features_unlocked": r == PRO,
        "control_plane": _control_plane_url(),
        "note": (
            "All analytics tools are free. Connectors and cloud artifact storage "
            "are Pro — subscribe at https://shubhamrandive.com."
            if r != PRO
            else "Pro is active — connectors and artifact storage are unlocked."
        ),
    }


def requires_pro(fn):
    """Decorator for Pro-only MCP tools (connectors, artifact storage).

    If the install isn't Pro, returns a clear upgrade message instead of
    running — never raises out to the host, so the agent gets a usable result.
    """
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_pro():
            return {
                "ok": False,
                "error": "pro_feature",
                "role": role(),
                "message": (
                    f"'{fn.__name__}' is a Pro feature (connectors + cloud artifact "
                    f"storage). Your current role is '{role()}'. Subscribe at "
                    "https://shubhamrandive.com to unlock it."
                ),
            }
        return fn(*args, **kwargs)

    return wrapper
