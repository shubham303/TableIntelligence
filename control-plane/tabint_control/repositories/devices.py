"""DevicesRepository — table access for `devices` only. No business logic
(the 2-device cap lives in the service, not here)."""
from __future__ import annotations

from datetime import datetime

from ..db.database import Database


class DevicesRepository:
    def __init__(self, db: Database):
        self._db = db

    def create_table(self) -> None:
        self._db.execute(
            """create table if not exists devices (
                id         varchar primary key,
                key_id     varchar not null,
                device_id  varchar not null,
                first_seen timestamp not null,
                last_seen  timestamp not null
            )"""
        )
        self._db.commit()

    def exists(self, key_id: str, device_id: str) -> bool:
        rows = self._db.execute(
            "select 1 from devices where key_id = ? and device_id = ?",
            (key_id, device_id),
        )
        return bool(rows)

    def count_for_key(self, key_id: str) -> int:
        rows = self._db.execute(
            "select count(*) from devices where key_id = ?", (key_id,)
        )
        return int(rows[0][0])

    def insert(
        self, device_row_id: str, key_id: str, device_id: str, when: datetime
    ) -> None:
        self._db.execute(
            "insert into devices (id, key_id, device_id, first_seen, last_seen) "
            "values (?, ?, ?, ?, ?)",
            (device_row_id, key_id, device_id, when, when),
        )
        self._db.commit()

    def touch(self, key_id: str, device_id: str, when: datetime) -> None:
        self._db.execute(
            "update devices set last_seen = ? where key_id = ? and device_id = ?",
            (when, key_id, device_id),
        )
        self._db.commit()
