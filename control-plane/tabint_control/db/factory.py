"""Factory + facade that hide the database choice from everything above.

`create_provider()` reads the environment, builds the correct `Database`, and
wraps it in a `RepositoryProvider` — the facade a service asks for its
repositories. The service never sees a `Database` or a connection string; it
only receives repositories, already wired to the right engine.

Environment selection (first match wins):
  * ``DATABASE_URL=postgres://…``  → Postgres/Neon (production)
  * ``TABINT_CONTROL_DB=/path.duckdb`` → DuckDB at that path (local dev)
  * otherwise → DuckDB at ``~/.tabint/control.duckdb`` (default local dev)
"""
from __future__ import annotations

import os
from pathlib import Path

from .database import Database, DuckDBDatabase, PostgresDatabase
from ..repositories.api_keys import ApiKeysRepository
from ..repositories.devices import DevicesRepository
from ..repositories.subscriptions import SubscriptionsRepository
from ..repositories.users import UsersRepository


def _default_local_path() -> str:
    p = Path.home() / ".tabint" / "control.duckdb"
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


def create_database(db_url: str | None = None) -> Database:
    """Build the concrete Database. Explicit ``db_url`` wins; else read env."""
    url = (db_url or "").strip()
    if not url:
        env_pg = os.environ.get("DATABASE_URL", "").strip()
        env_duck = os.environ.get("TABINT_CONTROL_DB", "").strip()
        url = env_pg or env_duck or _default_local_path()

    if url.startswith("postgres://") or url.startswith("postgresql://"):
        return PostgresDatabase(url)
    # treat anything else as a DuckDB file path (optionally duckdb:// prefixed)
    path = url[len("duckdb://"):] if url.startswith("duckdb://") else url
    return DuckDBDatabase(path)


class RepositoryProvider:
    """Facade over the repositories for one database. Services take this (or the
    individual repos from it) and stay ignorant of the backend."""

    def __init__(self, db: Database):
        self._db = db
        self._cache: dict = {}

    def _repo(self, cls):
        if cls not in self._cache:
            self._cache[cls] = cls(self._db)
        return self._cache[cls]

    @property
    def users(self) -> UsersRepository:
        return self._repo(UsersRepository)

    @property
    def api_keys(self) -> ApiKeysRepository:
        return self._repo(ApiKeysRepository)

    @property
    def devices(self) -> DevicesRepository:
        return self._repo(DevicesRepository)

    @property
    def subscriptions(self) -> SubscriptionsRepository:
        return self._repo(SubscriptionsRepository)

    def init_schema(self) -> None:
        """Create every table (each repository owns its own DDL)."""
        for repo in (self.users, self.api_keys, self.devices, self.subscriptions):
            repo.create_table()

    def close(self) -> None:
        self._db.close()


def create_provider(db_url: str | None = None) -> RepositoryProvider:
    """The one entry point callers use: env (or explicit url) → provider."""
    return RepositoryProvider(create_database(db_url))
