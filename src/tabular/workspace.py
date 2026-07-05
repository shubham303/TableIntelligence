"""Workspace — an in-memory DuckDB database holding one or more related tables.

A Workspace owns a single DuckDB connection and registers each uploaded CSV as
its own named table (each stamped with a ``_ti_row`` id, exposed through a view).
Because every table lives in one connection, foreign-key detection and future
cross-table joins are ordinary SQL — no materialising key columns into Python.

Each Workspace is **independent and per-session**: it uses its own in-memory
DuckDB database, so trained models and derived (write-back) columns never leak
between two Sessions — even when they load the same file.

A single-table session is just a Workspace with one table, so single- and
multi-table paths share the same code.

``Table`` is the per-table handle. It carries the analytics API (profile,
cluster, train_classifier, …); each method delegates to the analytics layer,
passing itself as the store-like object those functions expect (it exposes
``get_frame``, ``write_back_column``, ``run_sql`` and the ibis ``_table``).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import _ducktable
from .analytics import (
    association,
    clustering,
    descriptive,
    dimreduction,
    interpretation,
    supervised,
    timeseries,
)
from .identity import _lazy_import
from .relationships import find_join_edge
from .results import Result

ibis = _lazy_import("ibis")

# SQL reserved words that _sanitize must not emit as a bare identifier.
_RESERVED = frozenset({
    "all", "and", "any", "array", "as", "asc", "both", "case", "cast", "check",
    "collate", "column", "constraint", "create", "cross", "default", "desc",
    "distinct", "do", "else", "end", "except", "false", "fetch", "for", "foreign",
    "from", "full", "grant", "group", "having", "in", "inner", "intersect", "into",
    "is", "join", "lateral", "leading", "left", "like", "limit", "natural", "not",
    "null", "offset", "on", "only", "or", "order", "outer", "pivot", "primary",
    "references", "returning", "right", "select", "some", "table", "then", "to",
    "true", "union", "unique", "unpivot", "using", "user", "values", "view",
    "when", "where", "window", "with",
})


def _sanitize(name: str) -> str:
    """Turn a filename stem into a safe, non-reserved SQL identifier."""
    cleaned = re.sub(r"\W+", "_", name).strip("_").lower()
    if not cleaned:
        cleaned = "tbl"
    if cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"
    if cleaned in _RESERVED:
        cleaned = f"{cleaned}_tbl"
    return cleaned


class Table:
    """Handle to one table within a Workspace, plus the analytics it can run.

    The low-level methods (get_frame / write_back_column / run_sql / _table) make
    this object quack like the old single-table Store, so every analytics
    function works against it unchanged.
    """

    def __init__(self, workspace: "Workspace", name: str, internal: str, view: str) -> None:
        self._ws = workspace
        self.name = name
        self._internal = internal
        self._view = view
        self._table = workspace._ibis.table(view)  # ibis TableExpr for the view
        self.models: dict[str, Any] = {}

    def __repr__(self) -> str:
        return f"<Table {self.name!r} cols={list(self._table.schema().names)}>"

    # --- low-level (store-compatible) ------------------------------------- #

    def get_frame(self) -> Any:
        """Full table as a pandas DataFrame in stable _ti_row order."""
        return _ducktable.frame_in_order(self._ws._ibis, self._internal)

    def run_sql(self, query: str) -> Any:
        """Run SQL across the whole workspace (all tables are visible by name)."""
        return self._ws.run_sql(query)

    def write_back_column(self, name: str, values: Any) -> None:
        """Add or replace a column by row position (see _ducktable.write_back)."""
        _ducktable.write_back(self._ws._ibis, self._internal, self._view, name, values)
        self._table = self._ws._ibis.table(self._view)

    # --- descriptive ------------------------------------------------------ #

    def profile(self) -> Result:
        return descriptive.profile(self)

    def detect_outliers(self, column: str) -> Result:
        return descriptive.detect_outliers(self, column)

    def association_matrix(self) -> Result:
        return descriptive.association_matrix(self)

    # --- association ------------------------------------------------------ #

    def analyze_association(self, col_a: str, col_b: str) -> Result:
        return association.analyze_association(self, col_a, col_b)

    # --- clustering ------------------------------------------------------- #

    def cluster(self, n_clusters: int | None = None) -> Result:
        return clustering.cluster(self, n_clusters)

    def profile_clusters(self) -> Result:
        return clustering.profile_clusters(self)

    # --- supervised ------------------------------------------------------- #

    def train_classifier(self, target: str, name: str | None = None) -> Any:
        model = supervised.train_classifier(self, target)
        self.models[name or target] = model
        return model

    def train_regressor(self, target: str, name: str | None = None) -> Any:
        model = supervised.train_regressor(self, target)
        self.models[name or target] = model
        return model

    def evaluate(self, model_name: str) -> Result:
        return supervised.evaluate(self, self._model(model_name))

    def add_predictions(self, model_name: str, column_name: str | None = None) -> Result:
        model = self._model(model_name)
        frame = self.get_frame()
        preds = model.predict(frame[model._feature_names])
        col = column_name or f"{model_name}_pred"
        self.write_back_column(col, list(preds))
        return Result(
            method="add_predictions",
            summary=f"Wrote {len(preds)} predictions to column {col!r}",
            values={"column": col, "n": int(len(preds))},
            metadata={"model": model_name, "table": self.name},
        )

    # --- interpretation --------------------------------------------------- #

    def feature_importance(self, model_name: str) -> Result:
        return interpretation.feature_importance(self._model(model_name))

    def explain_prediction(self, model_name: str, row: Any) -> Result:
        return interpretation.explain_prediction(self._model(model_name), row)

    # --- dimensionality reduction ----------------------------------------- #

    def reduce_dimensions(self, method: str = "pca", n_components: int = 2) -> Result:
        return dimreduction.reduce_dimensions(self, method, n_components)

    # --- time series ------------------------------------------------------ #

    def decompose(self, time_column: str, value_column: str) -> Result:
        return timeseries.decompose(self, time_column, value_column)

    def forecast(self, time_column: str, value_column: str, horizon: int = 10) -> Result:
        return timeseries.forecast(self, time_column, value_column, horizon)

    # --- internals -------------------------------------------------------- #

    def _model(self, name: str) -> Any:
        if name not in self.models:
            raise KeyError(f"No model {name!r} on table {self.name!r}. Known: {list(self.models)}")
        return self.models[name]


class Workspace:
    """An in-memory DuckDB database holding one or more named tables.

    Each Workspace is independent: a fresh Session gets its own database, so
    models and derived (write-back) columns never leak between sessions.
    """

    def __init__(self, db_path: str | None = None) -> None:
        # db_path=None → in-memory (isolated library use); a path → persistent,
        # so tables and write-back columns survive across processes (CLI/MCP).
        self._ibis = ibis.duckdb.connect(db_path) if db_path else ibis.duckdb.connect()
        self._db_path = db_path
        self._tables: dict[str, Table] = {}
        if db_path:
            self._reattach()

    @classmethod
    def create(cls, paths: list[str], db_path: str | None = None) -> "Workspace":
        """Build a workspace holding the given CSVs as tables.

        Args:
            paths: CSV files to load as tables.
            db_path: On-disk DuckDB file for a persistent workspace, or None for
                an in-memory one.
        """
        resolved = [Path(p).resolve() for p in paths]
        if not resolved:
            raise ValueError("At least one CSV path is required.")
        ws = cls(db_path)
        for path in resolved:
            ws.add_csv(str(path))
        return ws

    def _reattach(self) -> None:
        """Rebuild Table handles from tables already present in a persisted DB."""
        names = set(self._ibis.list_tables())
        for view in names:
            if view.startswith("_tbl_"):
                continue  # internal table, not a public view
            if f"_tbl_{view}" in names:
                self._tables[view] = Table(self, view, f"_tbl_{view}", view)

    def close(self) -> None:
        """Close the underlying DuckDB connection (releases the file lock)."""
        try:
            self._ibis.con.close()
        except Exception:
            pass

    def add_csv(self, path: str, name: str | None = None) -> Table:
        """Load a CSV as a new table in this workspace and return its handle."""
        csv_path = Path(path).resolve()
        # Sanitize whether the name came from the caller or the filename stem, so
        # an explicit name can never introduce a reserved/spaced bare identifier.
        table_name = self._unique_name(_sanitize(name or csv_path.stem))
        internal = f"_tbl_{table_name}"
        _ducktable.load_csv(self._ibis, csv_path, internal, table_name)

        table = Table(self, table_name, internal, table_name)
        self._tables[table_name] = table
        return table

    def table(self, name: str) -> Table:
        """Return the handle for a named table."""
        if name not in self._tables:
            raise KeyError(f"No table {name!r}. Known: {self.table_names}")
        return self._tables[name]

    @property
    def table_names(self) -> list[str]:
        return list(self._tables)

    def run_sql(self, query: str) -> Any:
        """Run SQL against the workspace; every table is visible by its name."""
        return self._ibis.sql(query).execute()

    def relationships(self) -> Any:
        """Detect foreign-key relationships and return the connection graph."""
        from .relationships import detect_relationships
        return detect_relationships(self)

    def create_table(self, name: str, select_sql: str) -> Table:
        """Materialize an arbitrary SELECT as a new named table; return its handle.

        The escape hatch behind join(): any query over the workspace's tables can
        be frozen into a real table that every single-table analytic then works on.
        """
        table_name = self._unique_name(_sanitize(name))
        internal = f"_tbl_{table_name}"
        _ducktable.create_from_query(self._ibis, select_sql, internal, table_name)
        table = Table(self, table_name, internal, table_name)
        self._tables[table_name] = table
        return table

    def join(
        self,
        tables: list[str],
        name: str | None = None,
        how: str = "left",
    ) -> Table:
        """Join two or more tables along detected foreign keys into a new table.

        The join path is inferred from the foreign-key graph: tables are chained
        together on their FK↔PK columns. Overlapping column names are disambiguated
        by prefixing with the source table name. The result is a normal table, so
        every single-table operation (profile, cluster, train_*, …) runs on it.

        Args:
            tables: Names of the tables to join (2 or more).
            name: Name for the new table. Defaults to ``join_<t1>_<t2>_...``.
            how: SQL join type ("left", "inner").

        Returns:
            The Table handle for the joined result.
        """
        if len(tables) < 2:
            raise ValueError("join needs at least two tables.")
        missing = [t for t in tables if t not in self._tables]
        if missing:
            raise KeyError(f"Unknown tables: {missing}. Known: {self.table_names}")

        graph = self.relationships()
        from_sql = self._build_join_sql(tables, graph, how)
        projection = self._build_projection(tables)
        select_sql = f"SELECT {projection} FROM {from_sql}"
        return self.create_table(name or "join_" + "_".join(tables), select_sql)

    def _build_join_sql(self, tables: list[str], graph: Any, how: str) -> str:
        """Chain tables together on FK↔PK edges, greedily from the first table."""
        how_sql = how.upper()
        joined = [tables[0]]
        from_sql = _ducktable.quote_ident(tables[0])
        remaining = tables[1:]

        while remaining:
            for candidate in list(remaining):
                edge = find_join_edge(graph, joined, candidate)
                if edge is None:
                    continue
                left_tbl, left_col, right_col = edge
                from_sql += (
                    f' {how_sql} JOIN "{candidate}" '
                    f'ON "{left_tbl}"."{left_col}" = "{candidate}"."{right_col}"'
                )
                joined.append(candidate)
                remaining.remove(candidate)
                break
            else:
                raise ValueError(
                    f"No foreign-key path connects {remaining} to {joined}. "
                    "Use create_table(name, sql) for a manual join."
                )
        return from_sql

    def _build_projection(self, tables: list[str]) -> str:
        """Qualified column list; duplicate names get a unique <table>_ prefix."""
        seen: set[str] = set()
        cols: list[str] = []
        for tbl in tables:
            for col in self.table(tbl)._table.schema().names:
                target = col if col not in seen else f"{tbl}_{col}"
                # Guard against the prefixed name itself already existing.
                while target in seen:
                    target = f"{tbl}_{target}"
                seen.add(target)
                cols.append(f'"{tbl}"."{col}" AS "{target}"')
        return ", ".join(cols)

    def _unique_name(self, base: str) -> str:
        if base not in self._tables:
            return base
        i = 2
        while f"{base}_{i}" in self._tables:
            i += 1
        return f"{base}_{i}"
