"""ApiKeysRepository — table access for `api_keys` only. No business logic."""
from __future__ import annotations

from datetime import datetime

from ..db.database import Database


class ApiKeysRepository:
    def __init__(self, db: Database):
        self._db = db

    def create_table(self) -> None:
        self._db.execute(
            """create table if not exists api_keys (
                id         varchar primary key,
                user_id    varchar not null,
                key_hash   varchar unique not null,
                key_prefix varchar not null,
                tier       varchar not null,
                created_at timestamp not null,
                revoked_at timestamp
            )"""
        )
        self._db.commit()

    def get_by_hash(self, key_hash: str) -> tuple | None:
        """Return (id, user_id, tier, revoked_at) or None."""
        rows = self._db.execute(
            "select id, user_id, tier, revoked_at from api_keys where key_hash = ?",
            (key_hash,),
        )
        return rows[0] if rows else None

    def insert(
        self,
        key_id: str,
        user_id: str,
        key_hash: str,
        key_prefix: str,
        tier: str,
        created_at: datetime,
    ) -> None:
        self._db.execute(
            "insert into api_keys (id, user_id, key_hash, key_prefix, tier, created_at) "
            "values (?, ?, ?, ?, ?, ?)",
            (key_id, user_id, key_hash, key_prefix, tier, created_at),
        )
        self._db.commit()

    def set_tier_by_prefix(self, key_prefix: str, tier: str) -> int:
        found = self._db.execute(
            "select 1 from api_keys where key_prefix = ?", (key_prefix,)
        )
        self._db.execute(
            "update api_keys set tier = ? where key_prefix = ?", (tier, key_prefix)
        )
        self._db.commit()
        return len(found)

    def set_tier_by_user(self, user_id: str, tier: str) -> None:
        self._db.execute(
            "update api_keys set tier = ? where user_id = ?", (tier, user_id)
        )
        self._db.commit()

    def list_all(self) -> list[tuple]:
        """Return (key_prefix, user_id, tier, created_at) rows, oldest first."""
        return self._db.execute(
            "select key_prefix, user_id, tier, created_at from api_keys order by created_at"
        )
