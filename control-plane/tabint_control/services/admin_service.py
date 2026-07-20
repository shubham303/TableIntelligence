"""AdminService — mint keys, change tier, list keys. Depends only on repositories."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .. import security
from ..repositories.api_keys import ApiKeysRepository
from ..repositories.users import UsersRepository

TIERS = ("free", "trial", "paid", "expired")


class AdminService:
    def __init__(self, users: UsersRepository, api_keys: ApiKeysRepository):
        self._users = users
        self._api_keys = api_keys

    def _get_or_create_user(self, email: str) -> str:
        row = self._users.get_by_email(email)
        if row:
            return row[0]
        user_id = uuid.uuid4().hex
        self._users.insert(user_id, email, datetime.now(timezone.utc))
        return user_id

    def mint_key(self, email: str, tier: str = "trial") -> tuple[str, str]:
        """Create the user if needed + a new API key. Returns (plaintext, prefix).
        Only the hash is stored — the plaintext is shown once and never again."""
        if tier not in TIERS:
            raise ValueError(f"tier must be one of {TIERS}")
        user_id = self._get_or_create_user(email)
        plaintext = security.generate_key()
        prefix = security.display_prefix(plaintext)
        self._api_keys.insert(
            uuid.uuid4().hex,
            user_id,
            security.hash_key(plaintext),
            prefix,
            tier,
            datetime.now(timezone.utc),
        )
        return plaintext, prefix

    def set_tier(self, key_prefix: str, tier: str) -> int:
        if tier not in TIERS:
            raise ValueError(f"tier must be one of {TIERS}")
        return self._api_keys.set_tier_by_prefix(key_prefix, tier)

    def list_keys(self) -> list[dict]:
        """Compose key + owner email across two repositories (no cross-table SQL
        in either repository)."""
        out = []
        for key_prefix, user_id, tier, created_at in self._api_keys.list_all():
            user = self._users.get_by_id(user_id)
            email = user[1] if user else "?"
            out.append(
                {"key_prefix": key_prefix, "email": email, "tier": tier, "created_at": created_at}
            )
        return out
