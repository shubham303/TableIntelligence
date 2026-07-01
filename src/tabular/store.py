"""DuckDB-backed table store — the single owner of the loaded table.

This module is the only place where columns are added to the table (the
"materialize-as-column" mechanism). All analytics results that produce new
data (cluster labels, predictions, reduced dimensions) must write back here
via write_back_column rather than returning raw arrays.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .identity import fingerprint_dataframe, _lazy_import
from .loader import load

duckdb = _lazy_import("duckdb")

_STORE_SUBDIR = Path(".tableint") / "store"

# Internal table carries _ti_row (0-based row identity).
# The view exposes the same data without _ti_row so user SQL stays clean.
_INTERNAL = "_data"
_VIEW = "data"


def _csv_fingerprint(csv_path: Path) -> str:
    """16-char hex digest of the CSV's parsed content via fingerprint_dataframe."""
    return fingerprint_dataframe(load(str(csv_path)))


class Store:
    """DuckDB-backed store for a single table.

    Owns the connection and is the sole writer of columns. Other modules read
    via run_sql; they never write directly.

    Layout on disk:
        <csv_dir>/.tableint/store/<fingerprint>.duckdb

    Loading the same CSV content twice reuses the existing Store instance —
    no duplicate objects, no duplicate files, no DuckDB write-lock conflicts.

    Internally, the DuckDB file holds:
      - table ``_data``  — all columns plus a ``_ti_row`` integer (0-based row id)
      - view  ``data``   — ``_data`` minus ``_ti_row``; this is what callers query
    """

    _registry: dict[str, "Store"] = {}

    def __new__(cls, fingerprint: str) -> "Store":
        if fingerprint in cls._registry:
            return cls._registry[fingerprint]
        instance = super().__new__(cls)
        instance._conn = None
        cls._registry[fingerprint] = instance
        return instance

    def __init__(self, fingerprint: str) -> None:
        # __init__ runs even on cache hits; guard so we don't re-open.
        self._fingerprint = fingerprint

    @classmethod
    def for_csv(cls, path: str) -> "Store":
        """Return the Store for this CSV, creating it if needed."""
        csv_path = Path(path).resolve()
        fingerprint = _csv_fingerprint(csv_path)
        store = cls(fingerprint)
        store._open(csv_path, fingerprint)
        return store

    def _open(self, csv_path: Path, fingerprint: str) -> None:
        """Open (or reuse) the DuckDB connection and load the CSV if needed."""
        if self._conn is not None:
            return  # already open

        store_dir = csv_path.parent / _STORE_SUBDIR
        store_dir.mkdir(parents=True, exist_ok=True)
        db_path = store_dir / f"{fingerprint}.duckdb"

        self._conn = duckdb.connect(str(db_path))

        tables = {row[0] for row in self._conn.execute("SHOW TABLES").fetchall()}
        if _INTERNAL not in tables:
            self._conn.execute(
                f"CREATE TABLE {_INTERNAL} AS "
                f"SELECT row_number() OVER () - 1 AS _ti_row, * "
                f"FROM read_csv_auto('{csv_path}')"
            )
            self._conn.execute(
                f"CREATE VIEW {_VIEW} AS "
                f"SELECT * EXCLUDE (_ti_row) FROM {_INTERNAL}"
            )

    def load_csv(self, path: str) -> None:
        """Load a CSV file into the DuckDB store.

        Deprecated in favour of Store.for_csv(path); kept so existing call
        sites in Session continue to work during the transition.
        """
        csv_path = Path(path).resolve()
        fingerprint = _csv_fingerprint(csv_path)
        self._open(csv_path, fingerprint)

    def run_sql(self, query: str) -> Any:
        """Execute a SQL query and return the result as a pandas DataFrame.

        Args:
            query: SQL query string. The table is accessible as 'data'.

        Returns:
            pandas DataFrame with the query results.
        """
        return self._conn.execute(query).df()

    def write_back_column(self, name: str, values: Any) -> None:
        """Add or replace a column in the stored table.

        Uses an explicit row-id join inside DuckDB — no pandas round-trip.
        Length of values must match the table row count.

        Args:
            name: Column name to create or overwrite.
            values: Array-like of values, length must match the table row count.
        """
        col_list = list(values)
        n = len(col_list)

        # Build a temp table: (_ti_row INTEGER, <name> <inferred type>)
        # range(n) produces [0, 1, ..., n-1] — same order as the source rows.
        self._conn.execute(
            f"CREATE OR REPLACE TEMP TABLE _wb AS "
            f"SELECT unnest(range({n})) AS _ti_row, unnest(?) AS {name}",
            [col_list],
        )

        existing = {
            row[0]
            for row in self._conn.execute(f"DESCRIBE {_INTERNAL}").fetchall()
        }
        # Drop the old version of the column when overwriting.
        src_cols = f"{_INTERNAL}.* EXCLUDE ({name})" if name in existing else f"{_INTERNAL}.*"

        self._conn.execute(
            f"CREATE OR REPLACE TABLE {_INTERNAL} AS "
            f"SELECT {src_cols}, _wb.{name} "
            f"FROM {_INTERNAL} "
            f"JOIN _wb ON {_INTERNAL}._ti_row = _wb._ti_row"
        )
        # Rebuild the view so it reflects the new column.
        self._conn.execute(
            f"CREATE OR REPLACE VIEW {_VIEW} AS "
            f"SELECT * EXCLUDE (_ti_row) FROM {_INTERNAL}"
        )
        self._conn.execute("DROP TABLE IF EXISTS _wb")
