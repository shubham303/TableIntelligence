"""Low-level DuckDB table mechanics shared by Store and Workspace/Table.

Both the single-table Store and the multi-table Workspace need the same three
primitives: load a CSV into a table stamped with a stable row id, read it back in
that order, and write a computed column back by position. Keeping that logic here
means there is exactly one implementation of the ``_ti_row`` machinery.

Every table is stored as:
  - an internal table ``<internal>`` carrying a 0-based ``_ti_row`` id column
  - a view ``<view>`` = the internal table minus ``_ti_row`` (what callers query)

All identifiers (table, view, column names) are double-quoted before being spliced
into SQL, so names containing spaces, punctuation, or reserved words are handled
safely; the CSV path is single-quote-escaped for the same reason.

All functions take an ibis DuckDB backend; ``backend.con`` is the underlying
duckdb connection used for the low-level writes ibis doesn't cover.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np


def quote_ident(name: str) -> str:
    """Quote a SQL identifier, escaping embedded double quotes."""
    return '"' + str(name).replace('"', '""') + '"'


def _quote_literal(value: str) -> str:
    """Escape a value for use inside a single-quoted SQL string literal."""
    return value.replace("'", "''")


def load_csv(backend: Any, csv_path: Path, internal: str, view: str) -> None:
    """Create the internal table (with _ti_row) and its public view from a CSV."""
    path_literal = _quote_literal(str(csv_path))
    create_from_query(backend, f"SELECT * FROM read_csv_auto('{path_literal}')", internal, view)


def create_from_query(backend: Any, select_sql: str, internal: str, view: str) -> None:
    """Materialize a SELECT as a new internal table (with _ti_row) plus its view.

    Used for CSV loads and for derived tables such as joins — anything that
    produces rows and needs the same stable-row-id + hidden-view treatment.
    """
    qi, qv = quote_ident(internal), quote_ident(view)
    con = backend.con
    con.execute(
        f"CREATE TABLE {qi} AS "
        f"SELECT row_number() OVER () - 1 AS _ti_row, * FROM ({select_sql})"
    )
    con.execute(f"CREATE VIEW {qv} AS SELECT * EXCLUDE (_ti_row) FROM {qi}")


def frame_in_order(backend: Any, internal: str) -> Any:
    """Return the table as a pandas DataFrame in stable _ti_row order (id excluded)."""
    return backend.sql(
        f"SELECT * EXCLUDE (_ti_row) FROM {quote_ident(internal)} ORDER BY _ti_row"
    ).execute()


def write_back(backend: Any, internal: str, view: str, name: str, values: Any) -> None:
    """Add or replace a column by position (join on _ti_row), then refresh the view.

    ``values[i]`` is written to the row whose ``_ti_row`` is ``i`` — the same
    order frame_in_order returns, so per-row arrays align without realignment.

    Raises ValueError if len(values) != the table's row count, since a mismatch
    would silently drop rows through the positional inner join.
    """
    # DuckDB parameter binding can't consume numpy generics — coerce to Python.
    col_list = [v.item() if isinstance(v, np.generic) else v for v in values]
    n = len(col_list)
    con = backend.con
    qi, qv, qn = quote_ident(internal), quote_ident(view), quote_ident(name)
    tmp = quote_ident(f"_wb_{internal}")

    current = con.execute(f"SELECT COUNT(*) FROM {qi}").fetchone()[0]
    if n != current:
        raise ValueError(
            f"write_back_column expected {current} values (one per row) but got {n}."
        )

    con.execute(
        f"CREATE OR REPLACE TEMP TABLE {tmp} AS "
        f"SELECT unnest(range({n})) AS _ti_row, unnest(?) AS {qn}",
        [col_list],
    )
    existing = {row[0] for row in con.execute(f"DESCRIBE {qi}").fetchall()}
    src_cols = f"{qi}.* EXCLUDE ({qn})" if name in existing else f"{qi}.*"

    con.execute(
        f"CREATE OR REPLACE TABLE {qi} AS "
        f"SELECT {src_cols}, {tmp}.{qn} "
        f"FROM {qi} JOIN {tmp} ON {qi}._ti_row = {tmp}._ti_row"
    )
    con.execute(f"CREATE OR REPLACE VIEW {qv} AS SELECT * EXCLUDE (_ti_row) FROM {qi}")
    con.execute(f"DROP TABLE IF EXISTS {tmp}")
