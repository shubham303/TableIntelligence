"""MCP server exposing the deterministic core to agent tools (e.g. Claude Cowork).

The model is session-key centric, exactly as an agent expects: call
``create_session`` once to get a ``session_key``, then pass that key to every
later tool to identify the session and its data. Sessions are held live in an
in-memory registry for speed and backed by the on-disk persistence layer, so a
key keeps working across server restarts (a cache miss reopens it from disk).

Run with:  ``python -m tabular.mcp_server``  (stdio transport).
Set ``TABULAR_BASE`` to control where sessions are stored (default: cwd).
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import persistence
from ._serialize import jsonable as _jsonable, result_dict as _result
from .session import Session

_INSTRUCTIONS = """Deterministic single-table data analysis. Workflow:
1. create_session(paths) -> returns a session_key plus the tables and detected
   foreign-key relationships. Pass the session_key to every subsequent tool.
2. Every analytic runs on ONE table (an uploaded table or one produced by join).
   For multiple related tables, call join(session_key, tables) to materialize a
   combined table, then run analytics on it.
3. Each tool returns a structured result: the chosen method, a one-line summary,
   the values (statistics/scores), and metadata (assumptions, params). Trust the
   method it picked — test/algorithm selection is made deterministically."""

mcp = FastMCP("tabular", instructions=_INSTRUCTIONS)

_BASE = os.environ.get("TABULAR_BASE") or "."
_SESSIONS: dict[str, Session] = {}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _get(session_key: str) -> Session:
    """Resolve a session by key, reopening from disk on a cache miss."""
    session = _SESSIONS.get(session_key)
    if session is None:
        session = persistence.open_session(session_key, base=_BASE)  # raises if unknown
        _SESSIONS[session_key] = session
    return session


def _summary(session: Session) -> dict:
    return {
        "session_key": session.id,
        "tables": session.tables,
        "relationships": _jsonable(session.relationships().model_dump()),
    }


# --------------------------------------------------------------------------- #
# session lifecycle
# --------------------------------------------------------------------------- #

@mcp.tool()
def create_session(paths: list[str]) -> dict:
    """Create a session from one or more CSV paths. Returns the session_key,
    the loaded table names, and the auto-detected foreign-key relationships."""
    session = persistence.create_session(paths, base=_BASE)
    _SESSIONS[session.id] = session
    return _summary(session)


@mcp.tool()
def list_sessions() -> list[str]:
    """List the keys of all persisted sessions."""
    return persistence.list_sessions(base=_BASE)


@mcp.tool()
def session_info(session_key: str) -> dict:
    """Return a session's tables and detected relationships."""
    return _summary(_get(session_key))


@mcp.tool()
def add_table(session_key: str, path: str) -> dict:
    """Load another CSV into an existing session as a new table."""
    session = _get(session_key)
    table = session.add_table(path)
    return {"session_key": session_key, "added_table": table.name, "tables": session.tables}


# --------------------------------------------------------------------------- #
# structure: relationships, join, sql
# --------------------------------------------------------------------------- #

@mcp.tool()
def relationships(session_key: str) -> dict:
    """Detect and return the foreign-key graph across the session's tables."""
    return _jsonable(_get(session_key).relationships().model_dump())


@mcp.tool()
def join(session_key: str, tables: list[str], name: str | None = None, how: str = "left") -> dict:
    """Join tables along detected foreign keys into a new table; returns its name and columns."""
    joined = _get(session_key).join(tables, name=name, how=how)
    frame = joined.get_frame()
    return {"table": joined.name, "columns": list(frame.columns), "n_rows": int(len(frame))}


@mcp.tool()
def run_sql(session_key: str, query: str, limit: int = 1000) -> dict:
    """Run SQL across the session's tables (each visible by name). Rows are capped at `limit`."""
    frame = _get(session_key).run_sql(query)
    total = int(len(frame))
    records = _jsonable(frame.head(limit).to_dict(orient="records"))
    return {"n_rows": total, "truncated": total > limit, "rows": records}


# --------------------------------------------------------------------------- #
# descriptive
# --------------------------------------------------------------------------- #

@mcp.tool()
def profile(session_key: str, table: str) -> dict:
    """Profile every column of a table: type, missingness, cardinality, distribution."""
    return _result(_get(session_key).table(table).profile())


@mcp.tool()
def detect_outliers(session_key: str, table: str, column: str) -> dict:
    """Flag outliers in a numeric column (IQR + z-score) and write the flags back as a column."""
    return _result(_get(session_key).table(table).detect_outliers(column))


@mcp.tool()
def analyze_association(session_key: str, table: str, col_a: str, col_b: str) -> dict:
    """Test the association between two columns; the test is chosen from the dtype pair."""
    return _result(_get(session_key).table(table).analyze_association(col_a, col_b))


@mcp.tool()
def association_matrix(session_key: str, table: str) -> dict:
    """Pairwise association strength across all column pairs of a table."""
    return _result(_get(session_key).table(table).association_matrix())


# --------------------------------------------------------------------------- #
# clustering / dimensionality reduction
# --------------------------------------------------------------------------- #

@mcp.tool()
def cluster(session_key: str, table: str, n_clusters: int | None = None) -> dict:
    """Cluster rows (k-means; k auto-selected by silhouette if omitted) and write labels back."""
    return _result(_get(session_key).table(table).cluster(n_clusters))


@mcp.tool()
def profile_clusters(session_key: str, table: str) -> dict:
    """Characterize each cluster (requires cluster() to have been run first)."""
    return _result(_get(session_key).table(table).profile_clusters())


@mcp.tool()
def reduce_dimensions(session_key: str, table: str, method: str = "pca", n_components: int = 2) -> dict:
    """Reduce a table to a few components (pca/tsne/umap) and write them back as columns."""
    return _result(_get(session_key).table(table).reduce_dimensions(method, n_components))


# --------------------------------------------------------------------------- #
# supervised + interpretation
# --------------------------------------------------------------------------- #

@mcp.tool()
def train_classifier(session_key: str, table: str, target: str, name: str | None = None) -> dict:
    """Train a classifier on a table and persist it under `name` (default: target)."""
    return _train(session_key, table, target, name, "classification")


@mcp.tool()
def train_regressor(session_key: str, table: str, target: str, name: str | None = None) -> dict:
    """Train a regressor on a table and persist it under `name` (default: target)."""
    return _train(session_key, table, target, name, "regression")


def _train(session_key: str, table: str, target: str, name: str | None, task: str) -> dict:
    session = _get(session_key)
    handle = session.table(table)
    model_name = name or target
    if task == "classification":
        model = handle.train_classifier(target, name=model_name)
    else:
        model = handle.train_regressor(target, name=model_name)
    persistence.save_model(session, table, model_name, model)
    return {"model_name": model_name, "table": table, "target": target, "task": task,
            "features": model._feature_names}


@mcp.tool()
def evaluate(session_key: str, table: str, model_name: str) -> dict:
    """Evaluate a trained model on its held-out test split."""
    return _result(_get(session_key).table(table).evaluate(model_name))


@mcp.tool()
def feature_importance(session_key: str, table: str, model_name: str) -> dict:
    """Permutation feature importance for a trained model."""
    return _result(_get(session_key).table(table).feature_importance(model_name))


@mcp.tool()
def add_predictions(session_key: str, table: str, model_name: str, column_name: str | None = None) -> dict:
    """Write a trained model's predictions back onto the table as a new column."""
    return _result(_get(session_key).table(table).add_predictions(model_name, column_name))


@mcp.tool()
def explain_prediction(session_key: str, table: str, model_name: str, row_index: int = 0) -> dict:
    """Explain a single prediction with SHAP; row_index is the 0-based table row."""
    handle = _get(session_key).table(table)
    row = handle.get_frame().iloc[int(row_index)].to_dict()
    return _result(handle.explain_prediction(model_name, row))


# --------------------------------------------------------------------------- #
# time series
# --------------------------------------------------------------------------- #

@mcp.tool()
def decompose(session_key: str, table: str, time_column: str, value_column: str) -> dict:
    """Decompose a time series into trend / seasonality / residual."""
    return _result(_get(session_key).table(table).decompose(time_column, value_column))


@mcp.tool()
def forecast(session_key: str, table: str, time_column: str, value_column: str, horizon: int = 10) -> dict:
    """Forecast a time series forward `horizon` steps (ARIMA)."""
    return _result(_get(session_key).table(table).forecast(time_column, value_column, horizon))


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
