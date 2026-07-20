"""MCP server exposing the deterministic core to agent tools (e.g. Claude Cowork).

The model is session-key centric, exactly as an agent expects: call
``create_session`` once to get a ``session_key``, then pass that key to every
later tool to identify the session and its data. Sessions are held live in an
in-memory registry for speed and backed by the on-disk persistence layer, so a
key keeps working across server restarts (a cache miss reopens it from disk).

Run with:  ``python -m tabint.mcp_server``  (stdio transport).
Set ``TABULAR_BASE`` to control where sessions are stored (default: cwd).
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import connectors, entitlement, persistence, scratchpad
from . import platform as _platform
from ._serialize import jsonable as _jsonable, result_dict as _result
from .results import Result
from .session import Session

_INSTRUCTIONS = """Deterministic single-table data analysis. Workflow:
1. create_session(paths) -> returns a session_key plus the tables and detected
   foreign-key relationships. Pass the session_key to every subsequent tool.
2. Every analytic runs on ONE table (an uploaded table or one produced by join).
   For multiple related tables, call join(session_key, tables) to materialize a
   combined table, then run analytics on it.
3. Each tool returns a structured result: the chosen method, a one-line summary,
   the values (statistics/scores), and metadata (assumptions, params). Trust the
   method it picked — test/algorithm selection is made deterministically.
4. Every result also carries a `trust` block (a confidence level —
   high/moderate/low/none/unassessed — plus caveats) and a `declined` flag. When
   `declined` is true the data cannot support the question: report the refusal and
   its reason and do NOT substitute a number. Always convey the trust level and
   caveats to the user; never present a low-trust or declined result as a
   confident fact."""

mcp = FastMCP("tabint", instructions=_INSTRUCTIONS)

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
def account_status() -> dict:
    """Show this install's subscription tier and whether paid features
    (connectors, cloud artifact storage) are unlocked. All analytics tools are
    free; this only reports entitlement for the paid surface."""
    return entitlement.status()


# --------------------------------------------------------------------------- #
# connectors (paid) — pull a source into a session, normalized to the contract
# --------------------------------------------------------------------------- #

@mcp.tool()
def list_connectors() -> dict:
    """List available data-source connectors (e.g. 'stripe'). Connectors are a
    paid feature; analysis of local files is always free."""
    return {"connectors": connectors.list_connectors(), "paid_feature": True}


@mcp.tool()
@entitlement.requires_paid
def connect_stripe(limit: int = 1000, stripe_key: str | None = None) -> dict:
    """Pull your Stripe data (charges, customers, subscriptions, invoices) into a
    new analysis session, normalized to canonical tables. PAID feature.

    The key is read from STRIPE_API_KEY or TABINT_STRIPE_KEY if `stripe_key` is not
    passed (a test-mode `sk_test_...` key is fine to start). Your data is fetched
    directly from Stripe to this machine and never sent anywhere else. Then run the
    standard analytics tools on the returned session_key (see the 'stripe' prompt)."""
    import tempfile

    key = stripe_key or os.environ.get("TABINT_STRIPE_KEY") or os.environ.get("STRIPE_API_KEY")
    if not key:
        return {
            "ok": False,
            "error": "no_credentials",
            "message": "Set STRIPE_API_KEY (or TABINT_STRIPE_KEY) to a Stripe secret key "
                       "like sk_test_..., or pass stripe_key.",
        }
    conn = connectors.get_connector("stripe")
    tables = conn.fetch(key, limit=limit)
    dest = tempfile.mkdtemp(prefix="tabint_stripe_")
    paths = conn.materialize(tables, dest)
    session = persistence.create_session(list(paths.values()), base=_BASE)
    _SESSIONS[session.id] = session
    out = _summary(session)
    out["row_counts"] = {k: int(len(v)) for k, v in tables.items()}
    out["playbook"] = conn.platform_prompt
    return out


@mcp.prompt()
def stripe() -> str:
    """How to analyze data connected from Stripe."""
    return connectors.get_connector("stripe").platform_prompt


# --------------------------------------------------------------------------- #
# reports — save/organize analysis on the Table Intelligence platform
# (the MCP holds no user data; these call the website APIs with the user's key)
# --------------------------------------------------------------------------- #

_NEED_KEY = {
    "ok": False,
    "error": "not_configured",
    "message": "Set TABINT_API_KEY (from your account at shubhamrandive.com) to use reports.",
}


@mcp.tool()
def save_report(title: str, content: str, folder_id: str | None = None) -> dict:
    """Save a report to your Table Intelligence account to view later on the website
    dashboard. Needs an active trial or premium. `content` is the markdown report you
    compose from the analysis — ALWAYS include the findings together with their trust
    level and caveats (and note anything the tools declined to answer)."""
    return _platform.save_report(title, content, folder_id) if _platform.configured() else _NEED_KEY


@mcp.tool()
def list_reports(folder_id: str | None = None) -> dict:
    """List reports saved to your account (optionally within a folder)."""
    return _platform.list_reports(folder_id) if _platform.configured() else _NEED_KEY


@mcp.tool()
def get_report(report_id: str) -> dict:
    """Fetch a saved report's full content by id."""
    return _platform.get_report(report_id) if _platform.configured() else _NEED_KEY


@mcp.tool()
def create_folder(name: str) -> dict:
    """Create a folder in your account to organize reports."""
    return _platform.create_folder(name) if _platform.configured() else _NEED_KEY


@mcp.tool()
def list_folders() -> dict:
    """List your report folders."""
    return _platform.list_folders() if _platform.configured() else _NEED_KEY


# --------------------------------------------------------------------------- #
# outreach connector — manage prompts, prospects, and send email via the
# platform (data lives on the user's Table Intelligence account; sending uses
# their own connected email provider). A paid connector: needs trial/premium.
# --------------------------------------------------------------------------- #

_NEED_KEY_OUTREACH = {
    "ok": False,
    "error": "not_configured",
    "message": "Set TABINT_API_KEY (from your account at shubhamrandive.com) to use outreach.",
}


@mcp.tool()
@entitlement.requires_paid
def outreach_list_prompts() -> dict:
    """List your saved outreach prompts (the editable campaign playbooks)."""
    return _platform.list_outreach_prompts() if _platform.configured() else _NEED_KEY_OUTREACH


@mcp.tool()
@entitlement.requires_paid
def outreach_create_prompt(name: str, body: str) -> dict:
    """Create a new outreach prompt/playbook the agent can use to draft emails.
    `body` is the instruction text (tone, structure, qualification rules)."""
    return _platform.create_outreach_prompt(name, body) if _platform.configured() else _NEED_KEY_OUTREACH


@mcp.tool()
@entitlement.requires_paid
def outreach_update_prompt(prompt_id: str, name: str, body: str) -> dict:
    """Update an outreach prompt's name and body."""
    return _platform.update_outreach_prompt(prompt_id, name, body) if _platform.configured() else _NEED_KEY_OUTREACH


@mcp.tool()
@entitlement.requires_paid
def outreach_delete_prompt(prompt_id: str) -> dict:
    """Delete an outreach prompt by id."""
    return _platform.delete_outreach_prompt(prompt_id) if _platform.configured() else _NEED_KEY_OUTREACH


@mcp.tool()
@entitlement.requires_paid
def outreach_list_prospects(status: str | None = None) -> dict:
    """List prospects on the user's account, optionally filtered by status
    (new, drafted, sent, delivered, bounced, replied, skipped)."""
    return _platform.list_prospects(status) if _platform.configured() else _NEED_KEY_OUTREACH


@mcp.tool()
@entitlement.requires_paid
def outreach_save_prospects(prospects: list[dict]) -> dict:
    """Save one or many researched prospects to the user's account for review.
    Each item may include: name, email, company, research, draft_subject,
    draft_body, prompt_id, status. The user reviews/edits these in the dashboard
    before anything is sent."""
    return _platform.create_prospects(prospects) if _platform.configured() else _NEED_KEY_OUTREACH


@mcp.tool()
@entitlement.requires_paid
def outreach_get_prospect(prospect_id: str) -> dict:
    """Fetch one prospect's full record (research + drafted email + status)."""
    return _platform.get_prospect(prospect_id) if _platform.configured() else _NEED_KEY_OUTREACH


@mcp.tool()
@entitlement.requires_paid
def outreach_update_prospect(prospect_id: str, fields: dict) -> dict:
    """Update a prospect. `fields` may include name, email, company, research,
    draft_subject, draft_body, status, reply_text, prompt_id. Use this to record
    a reply (set reply_text and status='replied')."""
    return _platform.update_prospect(prospect_id, fields) if _platform.configured() else _NEED_KEY_OUTREACH


@mcp.tool()
@entitlement.requires_paid
def outreach_send(prospect_id: str) -> dict:
    """Send a prospect's drafted email via the user's connected email account.
    Fails cleanly if no account is connected or the draft is incomplete."""
    return _platform.send_prospect(prospect_id) if _platform.configured() else _NEED_KEY_OUTREACH


@mcp.tool()
@entitlement.requires_paid
def outreach_email_account() -> dict:
    """Show whether a sending email account is connected (never returns the key)."""
    return _platform.get_email_account() if _platform.configured() else _NEED_KEY_OUTREACH


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
# scratchpad: your own plain-text notebook for this session
# --------------------------------------------------------------------------- #

@mcp.tool()
def scratchpad_add(session_key: str, text: str) -> dict:
    """Append a note to this session's scratchpad — your own working memory.

    Write free-form English whenever you want to remember something across steps:
    a finding, a thing you tried and its outcome, a hypothesis, a reminder. Each
    note is stamped with the current date-time automatically. This is separate from
    the data — use it so you can pick up where you left off without recomputing.
    """
    _get(session_key)  # require a live session; raises if the key is unknown
    stamp = scratchpad.add(session_key, text)
    return {"session_key": session_key, "written_at": stamp}


@mcp.tool()
def scratchpad_read(session_key: str) -> dict:
    """Read back everything you've written to this session's scratchpad, in order."""
    _get(session_key)  # require a live session; raises if the key is unknown
    return {"session_key": session_key, "text": scratchpad.read(session_key)}


@mcp.tool()
def scratchpad_search(session_key: str, query: str) -> dict:
    """Search your scratchpad notes for `query` (simple case-insensitive text match).

    Returns the timestamped notes that mention the query — e.g. search "salary" to
    recall everything you noted about salary.
    """
    _get(session_key)  # require a live session; raises if the key is unknown
    return {"session_key": session_key, "matches": scratchpad.search(session_key, query)}


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
    """Run a read-only SQL SELECT across the session's tables (each visible by name).
    Rows are capped at `limit`. To build or fill tables, use create_table / insert_into."""
    frame = _get(session_key).run_sql(query)
    total = int(len(frame))
    records = _jsonable(frame.head(limit).to_dict(orient="records"))
    return {"n_rows": total, "truncated": total > limit, "rows": records}


@mcp.tool()
def create_table(
    session_key: str,
    name: str,
    columns: list[dict] | None = None,
    select_sql: str | None = None,
) -> dict:
    """Create a new clean, structured table in the session.

    Use this when the source data is messy or badly shaped: define the correct
    schema here, then copy the data across with insert_into (one query at a time
    or in bulk). run_sql cannot create tables — this is the tool that does.

    Two mutually exclusive modes (pass exactly one):
    - columns: an empty typed table. Each entry is {"name": "...", "type": "..."},
      e.g. [{"name": "order_id", "type": "BIGINT"}, {"name": "amount", "type": "DECIMAL(10,2)"}].
      Allowed types are the standard SQL/DuckDB types (INTEGER, BIGINT, DOUBLE,
      DECIMAL(p,s), VARCHAR, DATE, TIMESTAMP, BOOLEAN, ...).
    - select_sql: materialize a query over the existing tables as a new table in
      one shot (e.g. "SELECT trim(name) AS name, CAST(qty AS INTEGER) AS qty FROM raw").

    Returns the created table's name and columns.
    """
    cols = None
    if columns is not None:
        cols = [(c["name"], c["type"]) for c in columns]
    table = _get(session_key).create_table(name, columns=cols, select_sql=select_sql)
    frame = table.get_frame()
    return {"table": table.name, "columns": list(frame.columns), "n_rows": int(len(frame))}


@mcp.tool()
def insert_into(session_key: str, name: str, source_sql: str) -> dict:
    """Copy rows into an existing table (partner of create_table's `columns` mode).

    `source_sql` is a SELECT or VALUES query whose columns map positionally to the
    target table's columns, e.g.
      "SELECT trim(customer) AS name, CAST(spend AS DECIMAL(10,2)) FROM raw WHERE spend IS NOT NULL"
    or "VALUES ('Acme', 12.50), ('Globex', 9.99)".
    Call repeatedly to build a table up from many messy sources. Returns the
    number of rows inserted and the table's new total row count.
    """
    session = _get(session_key)
    inserted = session.insert_into(name, source_sql)
    total = int(len(session.table(name).get_frame()))
    return {"table": name, "inserted": inserted, "n_rows": total}


# --------------------------------------------------------------------------- #
# descriptive
# --------------------------------------------------------------------------- #

@mcp.tool()
def count_rows(session_key: str, table: str) -> dict:
    """Number of rows in a table — a cheap in-database COUNT(*), no data materialized.

    Use this instead of `profile` when you only need the row count (e.g. to size a
    table before an operation); it stays fast on arbitrarily large tables.
    """
    return {"table": table, "n_rows": _get(session_key).table(table).count_rows()}


@mcp.tool()
def count_non_null(session_key: str, table: str, column: str) -> dict:
    """Number of non-NULL (non-NaN) values in a column — an in-database COUNT(col).

    Returns the non-null count plus the row total and derived null count, all from
    a cheap COUNT with no data materialized. Fast on arbitrarily large tables.
    """
    t = _get(session_key).table(table)
    n_rows = t.count_rows()
    n_non_null = t.count_non_null(column)
    return {
        "table": table,
        "column": column,
        "n_non_null": n_non_null,
        "n_rows": n_rows,
        "n_null": n_rows - n_non_null,
    }


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
# feature computation: build new model-eligible columns from existing ones
# --------------------------------------------------------------------------- #

@mcp.tool()
def combine_columns(
    session_key: str, table: str, col_a: str, col_b: str, op: str, name: str | None = None
) -> dict:
    """Create a feature by combining two numeric columns with an arithmetic op.

    `op` is one of: add, subtract, multiply, divide, ratio. Division-by-zero
    becomes NaN. This is the primitive for most domain features — e.g.
    density = mass / volume: you supply the columns and the op, the arithmetic is
    generic. The new column is written back and is eligible for modelling.
    """
    return _result(_get(session_key).table(table).combine_columns(col_a, col_b, op, name))


@mcp.tool()
def transform_column(
    session_key: str, table: str, column: str, func: str, name: str | None = None
) -> dict:
    """Create a feature by applying a math transform to one numeric column.

    `func` is one of: log, log1p, sqrt, square, reciprocal, abs, zscore. Values
    outside a transform's domain (e.g. log of a non-positive) become NaN. Use log
    to tame skew, zscore to standardise, etc.
    """
    return _result(_get(session_key).table(table).transform_column(column, func, name))


@mcp.tool()
def bin_column(
    session_key: str,
    table: str,
    column: str,
    n_bins: int = 4,
    strategy: str = "quantile",
    name: str | None = None,
) -> dict:
    """Discretise a numeric column into ordinal bins (a categorical feature).

    `strategy` = "quantile" (equal-frequency) or "uniform" (equal-width). The new
    column holds 0-based integer bin indices.
    """
    return _result(_get(session_key).table(table).bin_column(column, n_bins, strategy, name))


@mcp.tool()
def expand_datetime(
    session_key: str, table: str, column: str, parts: list[str] | None = None
) -> dict:
    """Expand a datetime column into calendar-component features.

    `parts` (default: year, month, dayofweek, is_weekend) is any subset of: year,
    quarter, month, week, day, dayofweek, dayofyear, hour, is_weekend,
    is_month_start, is_month_end. Each becomes `<column>_<part>`.
    """
    return _result(_get(session_key).table(table).expand_datetime(column, parts))


@mcp.tool()
def group_aggregate(
    session_key: str,
    table: str,
    group_by: str,
    value: str,
    agg: str = "mean",
    name: str | None = None,
    add_deviation: bool = False,
) -> dict:
    """Aggregate `value` within each `group_by` category, broadcast back to rows.

    Every row receives its group's statistic (e.g. each order gets its customer's
    mean spend) — a strong relational feature. `agg` is one of mean, sum, min,
    max, std, median, count. With `add_deviation=True`, also writes
    `<value>_dev_from_<group_by>` = value − group mean.
    """
    return _result(
        _get(session_key).table(table).group_aggregate(group_by, value, agg, name, add_deviation)
    )


@mcp.tool()
def row_aggregate(
    session_key: str, table: str, columns: list[str], agg: str = "sum", name: str | None = None
) -> dict:
    """Aggregate several numeric columns across each row into one feature.

    `agg` is one of mean, sum, min, max, std, median, count (count = number of
    non-null inputs). The generic form of a total like "total atom count" from
    per-element count columns.
    """
    return _result(_get(session_key).table(table).row_aggregate(columns, agg, name))


@mcp.tool()
def normalize_fractions(
    session_key: str, table: str, columns: list[str], suffix: str = "_frac"
) -> dict:
    """Turn a set of count/amount columns into per-row fractions of their total.

    Each `<col>` becomes `<col><suffix>` = col / (row sum across the set), so the
    new columns sum to 1 per row. The generic form of composition fractions.
    """
    return _result(_get(session_key).table(table).normalize_fractions(columns, suffix))


@mcp.tool()
def compute_feature(session_key: str, table: str, name: str, expression: str) -> dict:
    """Create one feature column from a custom SQL scalar expression — the escape
    hatch when the fixed feature tools can't express what you need.

    `expression` is a DuckDB scalar expression over the table's columns, evaluated
    per row INSIDE the database (nothing is streamed to the app, so it scales to
    massive tables), and stored as a new model-eligible column `name`. Examples:
      - "mass / NULLIF(volume, 0)"
      - "CASE WHEN age >= 18 THEN 'adult' ELSE 'minor' END"
      - "avg(spend) OVER (PARTITION BY customer_id)"
      - "regexp_extract(email, '@(.*)$', 1)"

    Strictly feature generation: it must be a single scalar expression. Statement
    chaining, subqueries, DDL/DML, and file/catalog functions (read_csv, attach,
    install, ...) are rejected, and the expression must reference existing columns.
    """
    return _result(_get(session_key).table(table).compute_feature(name, expression))


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
def train_classifier(
    session_key: str, table: str, target: str, name: str | None = None, backend: str = "gbt"
) -> dict:
    """Train a classifier on a table and persist it under `name` (default: target).

    backend: "gbt" (default gradient-boosted trees) or "tabicl" (TabICL v2
    foundation model — no per-task training, strong on small/medium tables,
    needs the optional `tabicl` dependency).
    """
    return _train(session_key, table, target, name, "classification", backend)


@mcp.tool()
def train_regressor(
    session_key: str, table: str, target: str, name: str | None = None, backend: str = "gbt"
) -> dict:
    """Train a regressor on a table and persist it under `name` (default: target).

    backend: "gbt" (default gradient-boosted trees) or "tabicl" (TabICL v2
    foundation model — needs the optional `tabicl` dependency).
    """
    return _train(session_key, table, target, name, "regression", backend)


def _train(
    session_key: str, table: str, target: str, name: str | None, task: str, backend: str = "gbt"
) -> dict:
    session = _get(session_key)
    handle = session.table(table)
    model_name = name or target
    if task == "classification":
        model = handle.train_classifier(target, name=model_name, backend=backend)
    else:
        model = handle.train_regressor(target, name=model_name, backend=backend)
    if isinstance(model, Result):  # honesty seam declined training — surface it, don't save
        return _result(model)
    persistence.save_model(session, table, model_name, model)
    return {"model_name": model_name, "table": table, "target": target, "task": task,
            "backend": backend, "features": model._feature_names}


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


@mcp.tool()
def detect_changepoints(
    session_key: str, table: str, time_column: str, value_column: str, penalty: float = 10.0
) -> dict:
    """Detect points where a time series shifts behaviour (ruptures PELT).

    Needs the optional `insights` extra. Higher `penalty` = fewer changepoints.
    """
    return _result(_get(session_key).table(table).detect_changepoints(time_column, value_column, penalty))


# --------------------------------------------------------------------------- #
# insight primitives
# --------------------------------------------------------------------------- #

@mcp.tool()
def explain_metric(session_key: str, table: str, target: str, max_depth: int = 3) -> dict:
    """Explain a metric: ranked drivers + interpretable segment rules (shallow tree)."""
    return _result(_get(session_key).table(table).explain_metric(target, max_depth))


@mcp.tool()
def market_basket(
    session_key: str,
    table: str,
    transaction_column: str,
    item_column: str,
    min_support: float = 0.01,
    min_confidence: float = 0.2,
    max_rules: int = 50,
) -> dict:
    """Association-rule mining ("buy X → also buy Y"). Needs the optional `insights` extra."""
    return _result(_get(session_key).table(table).market_basket(
        transaction_column, item_column, min_support, min_confidence, max_rules))


@mcp.tool()
def causal_effect(
    session_key: str,
    table: str,
    treatment: str,
    outcome: str,
    confounders: list[str] | None = None,
) -> dict:
    """Estimate the causal effect of `treatment` on `outcome` (DoWhy backdoor).

    Needs the optional `insights` extra. Defaults confounders to all other features.
    """
    return _result(_get(session_key).table(table).causal_effect(treatment, outcome, confounders))


@mcp.tool()
def rfm(session_key: str, table: str, customer_column: str, date_column: str, monetary_column: str) -> dict:
    """RFM quintile segmentation of customers (Champions, At Risk, ...)."""
    return _result(_get(session_key).table(table).rfm(customer_column, date_column, monetary_column))


@mcp.tool()
def retention_cohorts(session_key: str, table: str, customer_column: str, date_column: str) -> dict:
    """Monthly retention matrix: first-purchase cohort × months-since."""
    return _result(_get(session_key).table(table).retention_cohorts(customer_column, date_column))


@mcp.tool()
def compare_periods(
    session_key: str, table: str, time_column: str, value_column: str, split: str | None = None
) -> dict:
    """Compare a metric before vs after a cut date (means, % change, significance)."""
    return _result(_get(session_key).table(table).compare_periods(time_column, value_column, split))


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
