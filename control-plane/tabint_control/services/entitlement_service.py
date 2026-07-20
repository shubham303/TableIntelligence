"""EntitlementService — business logic for validating a key + the device cap.

Depends only on repositories (never on a Database or a connection string). This
is the exact logic the production endpoint runs against Neon and the local
client runs against DuckDB — identical, because both get repositories from the
factory.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ..repositories.api_keys import ApiKeysRepository
from ..repositories.devices import DevicesRepository

DEVICE_CAP = 2

# Return values beyond the tiers.
DEVICE_LIMIT = "device_limit"
FREE = "free"


class EntitlementService:
    def __init__(self, api_keys: ApiKeysRepository, devices: DevicesRepository):
        self._api_keys = api_keys
        self._devices = devices

    def resolve(self, key_hash: str, device_id: str) -> str:
        """Effective tier for (key_hash, device_id). Enforces the 2-device cap
        and registers the device when allowed. Returns a tier, ``'free'`` for an
        unknown/revoked key, or ``'device_limit'`` when the cap is exceeded."""
        key = self._api_keys.get_by_hash(key_hash)
        if key is None:
            return FREE
        key_id, _user_id, tier, revoked_at = key
        if revoked_at is not None:
            return FREE

        now = datetime.now(timezone.utc)
        if self._devices.exists(key_id, device_id):
            self._devices.touch(key_id, device_id, now)
            return tier

        if self._devices.count_for_key(key_id) >= DEVICE_CAP:
            return DEVICE_LIMIT

        self._devices.insert(uuid.uuid4().hex, key_id, device_id, now)
        return tier
