"""DuckDB-backed table store — the single owner of the loaded table.

This module is the only place where columns are added to the table (the
"materialize-as-column" mechanism). All analytics results that produce new
data (cluster labels, predictions, reduced dimensions) must write back here
via write_back_column rather than returning raw arrays.

ibis is used as the query layer so callers work with Python expressions
rather than raw SQL strings. The DuckDB backend is the sole execution engine;
ibis.con exposes the underlying duckdb connection for low-level writes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import _ducktable
from .identity import fingerprint_dataframe, _lazy_import
from .loader import load

ibis = _lazy_import("ibis")

_STORE_SUBDIR = Path(".tableint") / "store"

# Internal table carries _ti_row (0-based row identity).
# The view exposes the same data without _ti_row so user SQL stays clean.
_INTERNAL = "_data"
_VIEW = "data"


def _csv_fingerprint(csv_path: Path) -> str:
    """16-char hex digest of the CSV's parsed content via fingerprint_dataframe."""
    return fingerprint_dataframe(load(str(csv_path)))


class Store:
    """ibis/DuckDB-backed store for a single table.

    Owns the ibis backend and is the sole writer of columns. Other modules
    read via run_sql or the ibis TableExpr at self._table; they never write
    directly.

    Layout on disk:
        <csv_dir>/.tableint/store/<fingerprint>.duckdb

    Loading the same CSV content twice reuses the existing Store instance —
    no duplicate objects, no duplicate files, no DuckDB write-lock conflicts.

    Internally, the DuckDB file holds:
      - table ``_data``  — all columns plus a ``_ti_row`` integer (0-based row id)
      - view  ``data``   — ``_data`` minus ``_ti_row``; this is what callers query

    Attributes:
        _ibis:  ibis DuckDB backend (use for ibis expressions and .sql())
        _table: ibis TableExpr for the user-facing ``data`` view
    """

    _registry: dict[str, "Store"] = {}

    def __new__(cls, fingerprint: str) -> "Store":
        if fingerprint in cls._registry:
            return cls._registry[fingerprint]
        instance = super().__new__(cls)
        instance._ibis = None
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
        """Open (or reuse) the ibis/DuckDB connection and load the CSV if needed."""
        if self._ibis is not None:
            return  # already open

        store_dir = csv_path.parent / _STORE_SUBDIR
        store_dir.mkdir(parents=True, exist_ok=True)
        db_path = store_dir / f"{fingerprint}.duckdb"

        self._ibis = ibis.duckdb.connect(str(db_path))

        if _INTERNAL not in self._ibis.list_tables():
            _ducktable.load_csv(self._ibis, csv_path, _INTERNAL, _VIEW)

        self._table = self._ibis.table(_VIEW)

    def load_csv(self, path: str) -> None:
        """Deprecated — use Store.for_csv(path) instead."""
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
        return self._ibis.sql(query).execute()

    def get_frame(self) -> Any:
        """Return the full table as a pandas DataFrame in stable row order.

        Rows come back ordered by the internal ``_ti_row`` id (0-based), so the
        i-th row of the frame corresponds to ``_ti_row = i``. This is the order
        write_back_column's positional join expects — any per-row array computed
        from this frame can be written straight back without realignment.

        The ``_ti_row`` column itself is excluded from the result.
        """
        return _ducktable.frame_in_order(self._ibis, _INTERNAL)

    def count_rows(self) -> int:
        """Row count via an in-database COUNT(*) — cheap, no rows materialized."""
        return _ducktable.count_rows(self._ibis, _VIEW)

    def count_non_null(self, column: str) -> int:
        """Count of non-NULL values in a column, computed inside DuckDB."""
        return _ducktable.count_non_null(self._ibis, _VIEW, column)

    def write_back_column(self, name: str, values: Any, feature: bool = False) -> None:
        """Add or replace a column in the stored table.

        Uses an explicit row-id join inside DuckDB — no pandas round-trip.
        Length of values must match the table row count.

        Args:
            name: Column name to create or overwrite.
            values: Array-like of values, length must match the table row count.
            feature: If False (default) the column is recorded as a derived
                annotation and excluded from feature matrices; pass True for
                derived columns meant to be features (e.g. reduced dimensions).
        """
        _ducktable.write_back(self._ibis, _INTERNAL, _VIEW, name, values)
        self._table = self._ibis.table(_VIEW)
        if feature:
            _ducktable.unregister_derived(self._ibis, _VIEW, name)
        else:
            _ducktable.register_derived(self._ibis, _VIEW, name)

    def add_computed_column(self, name: str, expression: str, feature: bool = True) -> int:
        """Materialize a SQL scalar expression as a new column, in-database.

        Runs entirely inside DuckDB over the stored table (no app-side
        materialization). The expression is validated to be a single scalar over
        the table's columns. Returns the count of non-null values.
        """
        n = _ducktable.add_computed_column(self._ibis, _INTERNAL, _VIEW, name, expression)
        self._table = self._ibis.table(_VIEW)
        if feature:
            _ducktable.unregister_derived(self._ibis, _VIEW, name)
        else:
            _ducktable.register_derived(self._ibis, _VIEW, name)
        return n

    def derived_columns(self) -> set[str]:
        """Names of derived (non-feature) columns; see write_back_column."""
        return _ducktable.derived_columns(self._ibis, _VIEW)
