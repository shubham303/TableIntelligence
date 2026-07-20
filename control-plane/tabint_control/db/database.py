"""DB facade — the ONLY place that knows a concrete database driver.

A `Database` exposes a tiny, dialect-neutral surface (`execute` / `commit` /
`close`) using ``?`` placeholders everywhere. Concrete subclasses adapt a driver:

  * `DuckDBDatabase`  — local development (a file; speaks SQL; zero setup).
  * `PostgresDatabase` — production (Neon).

Repositories depend only on this abstraction, so nothing above the DB layer
knows or cares which engine is in use. The factory (see ``factory.py``) picks
the concrete class from the environment.
"""
from __future__ import annotations

import abc


class Database(abc.ABC):
    """Dialect-neutral database handle. Use ``?`` placeholders in SQL."""

    @abc.abstractmethod
    def execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        """Run a statement; return rows (empty list for non-SELECT)."""

    @abc.abstractmethod
    def commit(self) -> None: ...

    @abc.abstractmethod
    def close(self) -> None: ...


class DuckDBDatabase(Database):
    """Local-dev backend backed by a DuckDB file. Native ``?`` placeholders."""

    def __init__(self, path: str):
        import duckdb  # already available via ibis-framework[duckdb]

        self._con = duckdb.connect(path)

    def execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        return self._con.execute(sql, list(params)).fetchall()

    def commit(self) -> None:
        self._con.commit()

    def close(self) -> None:
        self._con.close()


class PostgresDatabase(Database):
    """Production backend backed by Postgres/Neon. Rewrites ``?`` → ``%s``."""

    def __init__(self, dsn: str):
        import psycopg  # lazy: only prod needs the driver

        self._con = psycopg.connect(dsn)

    def execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        query = sql.replace("?", "%s")
        with self._con.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall() if cur.description else []

    def commit(self) -> None:
        self._con.commit()

    def close(self) -> None:
        self._con.close()
