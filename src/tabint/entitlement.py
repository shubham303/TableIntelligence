"""Entitlement / subscription gating for the Table Intelligence MCP server.

Local-first pricing model: all analytics tools are free forever; connectors and
cloud artifact storage are paid. This module answers one question — *is this
install entitled to paid features?* — by validating an API key against the
control plane (Supabase Edge Function ``validate-key``).

Design rules:
  * **Fails open to the free tier.** Any network/config error → ``free``. The
    server must never crash or block core analytics because auth was unreachable.
  * **Stdlib only** (``urllib``) — no new runtime dependency.
  * **Cached** with a periodic re-check so we don't hit the network per call.
  * **Device-bound.** A stable per-machine id is sent so the control plane can
    enforce the 2-device cap. Raw data is never sent — only key + device id.

Env:
  ``TABINT_API_KEY``            the user's key (absent → free tier)
  ``TABINT_CONTROL_PLANE_URL``  base URL of the control plane
                                (default: https://api.shubhamrandive.com)
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

FREE = "free"
TRIAL = "trial"
PAID = "paid"
EXPIRED = "expired"

# Tiers that unlock paid features (connectors, artifact storage).
_ENTITLED = {TRIAL, PAID}

_DEFAULT_CONTROL_PLANE = "https://shubhamrandive.com"
_RECHECK_SECONDS = 6 * 60 * 60  # re-validate at most every 6h
_TIMEOUT = 6  # network timeout (s); short so startup never hangs

# in-process cache: (tier, checked_at_monotonic)
_cache: tuple[str, float] | None = None


def _device_id() -> str:
    """Stable per-machine id, persisted at ~/.tabint/device (created once)."""
    path = Path.home() / ".tabint" / "device"
    try:
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
        path.parent.mkdir(parents=True, exist_ok=True)
        did = uuid.uuid4().hex
        path.write_text(did, encoding="utf-8")
        return did
    except OSError:
        # Non-persistable environment: fall back to a per-process id. The user
        # may burn a device slot per run here, but it never blocks the server.
        return "ephemeral-" + uuid.uuid4().hex


def _control_plane_url() -> str:
    return (os.environ.get("TABINT_CONTROL_PLANE_URL") or _DEFAULT_CONTROL_PLANE).rstrip("/")


def _validate_remote(api_key: str) -> str:
    """Call the control plane; return a tier string. Raises on any failure."""
    url = f"{_control_plane_url()}/api/validate-key"
    payload = json.dumps({"api_key": api_key, "device_id": _device_id()}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    tier = str(body.get("tier", FREE)).lower()
    return tier if tier in {FREE, TRIAL, PAID, EXPIRED} else FREE


def _local_mode() -> bool:
    """Use a local DB (dev) when a control-plane DB is configured in the env."""
    return bool(
        os.environ.get("TABINT_CONTROL_DB", "").strip()
        or os.environ.get("DATABASE_URL", "").strip()
    )


def _validate_local(api_key: str) -> str:
    """Resolve via the control-plane EntitlementService against the local DB.
    Lazy-imports tabint_control (a dev-only package); raises if unavailable so
    the caller falls open to free."""
    from tabint_control import create_provider, security  # dev-only
    from tabint_control.services import EntitlementService

    provider = create_provider()
    try:
        svc = EntitlementService(provider.api_keys, provider.devices)
        return svc.resolve(security.hash_key(api_key), _device_id())
    finally:
        provider.close()


def tier(force: bool = False) -> str:
    """Current entitlement tier, cached with a periodic re-check.

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
        if _local_mode():
            resolved = _validate_local(api_key)   # dev: direct DuckDB via the service
        else:
            resolved = _validate_remote(api_key)  # prod: HTTP to shubham-site
    except Exception:  # noqa: BLE001 - fail-open is the whole point; never raise
        # Keep a previous good tier if we have one, else fall open to free.
        resolved = _cache[0] if _cache is not None else FREE
    _cache = (resolved, now)
    return resolved


def is_paid() -> bool:
    """True if the install is entitled to paid features (trial or paid)."""
    return tier() in _ENTITLED


def status() -> dict:
    """Human-facing entitlement summary (for an ``account_status`` tool)."""
    t = tier()
    local = _local_mode()
    return {
        "tier": t,
        "paid_features_unlocked": t in _ENTITLED,
        "device_id": _device_id(),
        "mode": "local" if local else "remote",
        "control_plane": (
            os.environ.get("TABINT_CONTROL_DB") or os.environ.get("DATABASE_URL")
            if local
            else _control_plane_url()
        ),
        "note": (
            "All analytics tools are free. Connectors and cloud artifact storage "
            "require an active subscription — start one at https://shubhamrandive.com."
            if t not in _ENTITLED
            else "Subscription active — connectors and artifact storage are unlocked."
        ),
    }


class PaidFeatureRequired(Exception):
    """Raised internally when a paid tool is used without entitlement."""


def requires_paid(fn):
    """Decorator for paid MCP tools (connectors, artifact storage).

    If the install isn't entitled, returns a clear upgrade message instead of
    running — never raises out to the host, so the agent gets a usable result.
    """
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_paid():
            return {
                "ok": False,
                "error": "paid_feature",
                "tier": tier(),
                "message": (
                    f"'{fn.__name__}' is a paid feature (connectors + cloud artifact "
                    "storage). Your current tier is "
                    f"'{tier()}'. Start a subscription or free trial at "
                    "https://shubhamrandive.com to unlock it."
                ),
            }
        return fn(*args, **kwargs)

    return wrapper
