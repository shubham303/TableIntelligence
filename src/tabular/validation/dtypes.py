"""Column type classification — the single source of truth for dtype routing.

Every analytics function that needs to know "is this column categorical or
continuous?" must call classify_column here. No local re-implementation of
this logic is permitted. This prevents the most common source of inconsistency
in tabular analysis pipelines.

Classification runs entirely inside DuckDB via ibis expressions — no column
data is ever pulled into Python memory, so large tables are handled safely.
"""
from __future__ import annotations

import ibis.expr.datatypes as dt

# Vocabulary of column types returned by classify_column.
COLUMN_TYPES = frozenset({
    "continuous",
    "categorical_nominal",
    "categorical_ordinal",
    "datetime",
    "identifier",
})

# A string column whose distinct-value ratio exceeds this threshold is treated
# as an identifier (e.g. UUIDs, email addresses, primary keys).
_IDENTIFIER_DISTINCT_RATIO = 0.9

# A numeric column with at most this many distinct values is treated as
# categorical rather than continuous.
_NUMERIC_CATEGORICAL_MAX_DISTINCT = 15


def classify_column(col_name: str, store: object) -> str:
    """Classify a single column into a canonical type.

    Uses ibis expressions against the DuckDB backend — no data is
    materialised into Python memory.

    Args:
        col_name: Name of the column to classify.
        store:    A Store instance (provides store._table ibis TableExpr).

    Returns:
        One of: "continuous", "categorical_nominal", "categorical_ordinal",
        "datetime", "identifier".
    """
    table = store._table
    dtype = table.schema()[col_name]

    # Temporal types — classify immediately from schema, no query needed.
    if isinstance(dtype, (dt.Timestamp, dt.Date, dt.Time)):
        return "datetime"

    # Boolean — always categorical.
    if isinstance(dtype, dt.Boolean):
        return "categorical_nominal"

    col = table[col_name]

    # Numeric types.
    if isinstance(dtype, (dt.Integer, dt.Floating, dt.Decimal)):
        n_distinct = col.nunique().execute()
        return "continuous" if n_distinct > _NUMERIC_CATEGORICAL_MAX_DISTINCT else "categorical_nominal"

    # String types.
    if isinstance(dtype, dt.String):
        n_rows = table.count().execute()
        n_distinct = col.nunique().execute()
        if n_rows > 0 and (n_distinct / n_rows) > _IDENTIFIER_DISTINCT_RATIO:
            return "identifier"
        return "categorical_nominal"

    # Fallback for any other type (arrays, structs, etc.).
    return "categorical_nominal"


def classify_table(store: object) -> dict[str, str]:
    """Classify every column in the store's table.

    Args:
        store: A Store instance.

    Returns:
        Mapping of column name → type string (same vocabulary as classify_column).
    """
    return {
        col: classify_column(col, store)
        for col in store._table.schema()
    }
