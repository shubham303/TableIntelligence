"""UsersRepository — table access for `users` only. No business logic."""
from __future__ import annotations

from datetime import datetime

from ..db.database import Database


class UsersRepository:
    def __init__(self, db: Database):
        self._db = db

    def create_table(self) -> None:
        self._db.execute(
            """create table if not exists users (
                id                 varchar primary key,
                email              varchar unique not null,
                stripe_customer_id varchar,
                created_at         timestamp not null
            )"""
        )
        self._db.commit()

    def get_by_email(self, email: str) -> tuple | None:
        rows = self._db.execute("select id from users where email = ?", (email,))
        return rows[0] if rows else None

    def get_by_id(self, user_id: str) -> tuple | None:
        rows = self._db.execute(
            "select id, email, stripe_customer_id from users where id = ?", (user_id,)
        )
        return rows[0] if rows else None

    def insert(self, user_id: str, email: str, created_at: datetime) -> None:
        self._db.execute(
            "insert into users (id, email, created_at) values (?, ?, ?)",
            (user_id, email, created_at),
        )
        self._db.commit()

    def set_stripe_customer(self, user_id: str, stripe_customer_id: str) -> None:
        self._db.execute(
            "update users set stripe_customer_id = ? where id = ?",
            (stripe_customer_id, user_id),
        )
        self._db.commit()
