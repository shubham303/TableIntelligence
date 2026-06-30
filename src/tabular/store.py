"""DuckDB-backed table store — the single owner of the loaded table.

This module is the only place where columns are added to the table (the
"materialize-as-column" mechanism). All analytics results that produce new
data (cluster labels, predictions, reduced dimensions) must write back here
via write_back_column rather than returning raw arrays.
"""
from __future__ import annotations

from typing import Any


class Store:
    """DuckDB-backed store for a single table.

    Owns the connection and is the sole writer of columns. Other modules read
    via run_sql; they never write directly.
    """

    def __init__(self) -> None:
        self._conn: Any = None
        self._table_name: str = "data"

    def load_csv(self, path: str) -> None:
        """Load a CSV file into the DuckDB store.

        Args:
            path: Path to the CSV file.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def run_sql(self, query: str) -> Any:
        """Execute a SQL query and return the result.

        Args:
            query: SQL query string. The table is accessible as 'data'.

        Returns:
            Query result (pandas DataFrame or DuckDB relation).
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def write_back_column(self, name: str, values: Any) -> None:
        """Add or replace a column in the stored table.

        Args:
            name: Column name to create or overwrite.
            values: Array-like of values, length must match the table row count.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")
