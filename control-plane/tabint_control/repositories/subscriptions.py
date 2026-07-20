"""SubscriptionsRepository — table access for `subscriptions` only.
Filled out in the Stripe phase (0.5); schema + basic access defined now."""
from __future__ import annotations

from datetime import datetime

from ..db.database import Database


class SubscriptionsRepository:
    def __init__(self, db: Database):
        self._db = db

    def create_table(self) -> None:
        self._db.execute(
            """create table if not exists subscriptions (
                id                     varchar primary key,
                user_id                varchar not null,
                stripe_subscription_id varchar,
                status                 varchar not null,
                trial_ends_at          timestamp,
                current_period_end     timestamp,
                created_at             timestamp not null,
                updated_at             timestamp not null
            )"""
        )
        self._db.commit()

    def get_by_user(self, user_id: str) -> tuple | None:
        rows = self._db.execute(
            "select id, stripe_subscription_id, status, trial_ends_at, current_period_end "
            "from subscriptions where user_id = ?",
            (user_id,),
        )
        return rows[0] if rows else None

    def upsert(
        self,
        sub_id: str,
        user_id: str,
        stripe_subscription_id: str | None,
        status: str,
        trial_ends_at: datetime | None,
        current_period_end: datetime | None,
        now: datetime,
    ) -> None:
        existing = self.get_by_user(user_id)
        if existing:
            self._db.execute(
                "update subscriptions set stripe_subscription_id = ?, status = ?, "
                "trial_ends_at = ?, current_period_end = ?, updated_at = ? where user_id = ?",
                (stripe_subscription_id, status, trial_ends_at, current_period_end, now, user_id),
            )
        else:
            self._db.execute(
                "insert into subscriptions (id, user_id, stripe_subscription_id, status, "
                "trial_ends_at, current_period_end, created_at, updated_at) "
                "values (?, ?, ?, ?, ?, ?, ?, ?)",
                (sub_id, user_id, stripe_subscription_id, status, trial_ends_at,
                 current_period_end, now, now),
            )
        self._db.commit()
