"""Command-line surface — lets a terminal agent (e.g. Claude Code) drive the core.

Every command prints a JSON object to stdout so an agent can parse the result.
State lives in on-disk sessions (see tabint.persistence): ``tabint load`` mints a
session key; pass ``--session <key>`` to every later command to keep working on the
same data. Analytics operate on ONE table (``--table``) — an uploaded table or one
produced by ``tabint join``.

Examples::

    tabint load orders.csv customers.csv          # -> {"session_key": "s_ab12", ...}
    tabint relationships --session s_ab12
    tabint join orders customers --session s_ab12 --name enriched
    tabint associate order_total tier --session s_ab12 --table enriched
    tabint train-classifier is_churned --session s_ab12 --table customers --name churn
    tabint evaluate --session s_ab12 --table customers --model churn
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import persistence, scratchpad
from ._serialize import jsonable, result_dict


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2))


def _open(args) -> Any:
    return persistence.open_session(args.session, base=args.base)


# --------------------------------------------------------------------------- #
# command handlers — each returns a JSON-able dict
# --------------------------------------------------------------------------- #

def _cmd_load(args) -> dict:
    s = persistence.create_session(args.paths, base=args.base)
    return {
        "session_key": s.id,
        "tables": s.tables,
        "relationships": jsonable(s.relationships().model_dump()),
    }


def _cmd_sessions(args) -> list:
    return persistence.list_sessions(base=args.base)


def _cmd_info(args) -> dict:
    s = _open(args)
    return {"session_key": s.id, "tables": s.tables,
            "relationships": jsonable(s.relationships().model_dump())}


def _cmd_add_table(args) -> dict:
    s = _open(args)
    t = s.add_table(args.path)
    return {"session_key": s.id, "added_table": t.name, "tables": s.tables}


def _cmd_scratchpad_add(args) -> dict:
    _open(args)  # require an existing session; raises if the key is unknown
    return {"session_key": args.session, "written_at": scratchpad.add(args.session, args.text)}


def _cmd_scratchpad_read(args) -> dict:
    _open(args)  # require an existing session; raises if the key is unknown
    return {"session_key": args.session, "text": scratchpad.read(args.session)}


def _cmd_scratchpad_search(args) -> dict:
    _open(args)  # require an existing session; raises if the key is unknown
    return {"session_key": args.session, "matches": scratchpad.search(args.session, args.query)}


def _cmd_relationships(args) -> dict:
    return jsonable(_open(args).relationships().model_dump())


def _cmd_join(args) -> dict:
    j = _open(args).join(args.tables, name=args.name, how=args.how)
    frame = j.get_frame()
    return {"table": j.name, "columns": list(frame.columns), "n_rows": int(len(frame))}


def _cmd_sql(args) -> dict:
    frame = _open(args).run_sql(args.query)
    total = int(len(frame))
    return {"n_rows": total, "truncated": total > args.limit,
            "rows": jsonable(frame.head(args.limit).to_dict(orient="records"))}


def _cmd_create_table(args) -> dict:
    columns = None
    if args.column:
        columns = []
        for spec in args.column:
            if ":" not in spec:
                raise SystemExit(f"--column expects NAME:TYPE, got {spec!r}")
            col, sql_type = spec.split(":", 1)
            columns.append((col.strip(), sql_type.strip()))
    t = _open(args).create_table(args.name, columns=columns, select_sql=args.select_sql)
    frame = t.get_frame()
    return {"table": t.name, "columns": list(frame.columns), "n_rows": int(len(frame))}


def _cmd_insert_into(args) -> dict:
    s = _open(args)
    inserted = s.insert_into(args.name, args.source_sql)
    return {"table": args.name, "inserted": inserted,
            "n_rows": int(len(s.table(args.name).get_frame()))}


def _cmd_count_rows(args) -> dict:
    return {"table": args.table, "n_rows": _open(args).table(args.table).count_rows()}


def _cmd_count_non_null(args) -> dict:
    t = _open(args).table(args.table)
    n_rows = t.count_rows()
    n_non_null = t.count_non_null(args.column)
    return {"table": args.table, "column": args.column, "n_non_null": n_non_null,
            "n_rows": n_rows, "n_null": n_rows - n_non_null}


def _cmd_profile(args) -> dict:
    return result_dict(_open(args).table(args.table).profile())


def _cmd_outliers(args) -> dict:
    return result_dict(_open(args).table(args.table).detect_outliers(args.column))


def _cmd_associate(args) -> dict:
    return result_dict(_open(args).table(args.table).analyze_association(args.col_a, args.col_b))


def _cmd_assoc_matrix(args) -> dict:
    return result_dict(_open(args).table(args.table).association_matrix())


def _cmd_combine_columns(args) -> dict:
    return result_dict(
        _open(args).table(args.table).combine_columns(args.col_a, args.col_b, args.op, args.name)
    )


def _cmd_transform_column(args) -> dict:
    return result_dict(
        _open(args).table(args.table).transform_column(args.column, args.func, args.name)
    )


def _cmd_bin_column(args) -> dict:
    return result_dict(
        _open(args).table(args.table).bin_column(args.column, args.n_bins, args.strategy, args.name)
    )


def _cmd_expand_datetime(args) -> dict:
    return result_dict(_open(args).table(args.table).expand_datetime(args.column, args.parts))


def _cmd_group_aggregate(args) -> dict:
    return result_dict(
        _open(args)
        .table(args.table)
        .group_aggregate(args.group_by, args.value, args.agg, args.name, args.add_deviation)
    )


def _cmd_row_aggregate(args) -> dict:
    return result_dict(_open(args).table(args.table).row_aggregate(args.columns, args.agg, args.name))


def _cmd_normalize_fractions(args) -> dict:
    return result_dict(_open(args).table(args.table).normalize_fractions(args.columns, args.suffix))


def _cmd_compute_feature(args) -> dict:
    return result_dict(_open(args).table(args.table).compute_feature(args.name, args.expression))


def _cmd_cluster(args) -> dict:
    return result_dict(_open(args).table(args.table).cluster(args.n_clusters))


def _cmd_profile_clusters(args) -> dict:
    return result_dict(_open(args).table(args.table).profile_clusters())


def _cmd_reduce(args) -> dict:
    return result_dict(_open(args).table(args.table).reduce_dimensions(args.method, args.n_components))


def _cmd_train(task: str):
    def run(args) -> dict:
        s = _open(args)
        handle = s.table(args.table)
        model_name = args.name or args.target
        model = (handle.train_classifier if task == "classification" else handle.train_regressor)(
            args.target, name=model_name, backend=args.backend
        )
        persistence.save_model(s, args.table, model_name, model)
        return {"model_name": model_name, "table": args.table, "target": args.target,
                "task": task, "backend": args.backend, "features": model._feature_names}
    return run


def _cmd_evaluate(args) -> dict:
    return result_dict(_open(args).table(args.table).evaluate(args.model))


def _cmd_importance(args) -> dict:
    return result_dict(_open(args).table(args.table).feature_importance(args.model))


def _cmd_predict(args) -> dict:
    return result_dict(_open(args).table(args.table).add_predictions(args.model, args.column))


def _cmd_explain(args) -> dict:
    handle = _open(args).table(args.table)
    row = handle.get_frame().iloc[args.row].to_dict()
    return result_dict(handle.explain_prediction(args.model, row))


def _cmd_decompose(args) -> dict:
    return result_dict(_open(args).table(args.table).decompose(args.time, args.value))


def _cmd_forecast(args) -> dict:
    return result_dict(_open(args).table(args.table).forecast(args.time, args.value, args.horizon))


def _cmd_changepoints(args) -> dict:
    return result_dict(_open(args).table(args.table).detect_changepoints(args.time, args.value, args.penalty))


def _cmd_explain_metric(args) -> dict:
    return result_dict(_open(args).table(args.table).explain_metric(args.target, args.max_depth))


def _cmd_market_basket(args) -> dict:
    return result_dict(_open(args).table(args.table).market_basket(
        args.transaction, args.item, args.min_support, args.min_confidence, args.max_rules))


def _cmd_causal(args) -> dict:
    confounders = args.confounders.split(",") if args.confounders else None
    return result_dict(_open(args).table(args.table).causal_effect(args.treatment, args.outcome, confounders))


def _cmd_rfm(args) -> dict:
    return result_dict(_open(args).table(args.table).rfm(args.customer, args.date, args.monetary))


def _cmd_retention(args) -> dict:
    return result_dict(_open(args).table(args.table).retention_cohorts(args.customer, args.date))


def _cmd_compare_periods(args) -> dict:
    return result_dict(_open(args).table(args.table).compare_periods(args.time, args.value, args.split))


# --------------------------------------------------------------------------- #
# parser
# --------------------------------------------------------------------------- #

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tabint", description="Deterministic single-table data analysis.")
    p.add_argument("--base", default=".", help="Root dir holding .tableint/sessions (default: cwd).")
    sub = p.add_subparsers(dest="command", required=True)

    def with_session(sp):
        sp.add_argument("--session", required=True, help="Session key from `tabint load`.")
        return sp

    def with_table(sp):
        sp.add_argument("--table", required=True, help="Table to operate on.")
        return sp

    sp = sub.add_parser("load", help="Load CSV(s) into a new session.")
    sp.add_argument("paths", nargs="+")
    sp.set_defaults(func=_cmd_load)

    sub.add_parser("sessions", help="List session keys.").set_defaults(func=_cmd_sessions)

    with_session(sub.add_parser("info", help="Session tables + relationships.")).set_defaults(func=_cmd_info)

    sp = with_session(sub.add_parser("add-table", help="Add a CSV to a session."))
    sp.add_argument("path")
    sp.set_defaults(func=_cmd_add_table)

    # --- scratchpad: the agent's own plain-text notebook for the session ---
    sp = with_session(sub.add_parser("scratchpad-add", help="Append a timestamped note."))
    sp.add_argument("text")
    sp.set_defaults(func=_cmd_scratchpad_add)

    with_session(sub.add_parser("scratchpad-read", help="Read the whole scratchpad.")).set_defaults(func=_cmd_scratchpad_read)

    sp = with_session(sub.add_parser("scratchpad-search", help="Text-search scratchpad notes."))
    sp.add_argument("query")
    sp.set_defaults(func=_cmd_scratchpad_search)

    with_session(sub.add_parser("relationships", help="Detect the FK graph.")).set_defaults(func=_cmd_relationships)

    sp = with_session(sub.add_parser("join", help="Join tables along FKs into a new table."))
    sp.add_argument("tables", nargs="+")
    sp.add_argument("--name", default=None)
    sp.add_argument("--how", default="left")
    sp.set_defaults(func=_cmd_join)

    sp = with_session(sub.add_parser("sql", help="Run a read-only SQL SELECT over the session."))
    sp.add_argument("query")
    sp.add_argument("--limit", type=int, default=1000)
    sp.set_defaults(func=_cmd_sql)

    sp = with_session(sub.add_parser(
        "create-table", help="Create a clean table from a schema or a SELECT."))
    sp.add_argument("name")
    sp.add_argument("--column", action="append", metavar="NAME:TYPE",
                    help="A column for an empty table (repeatable), e.g. --column amount:DECIMAL(10,2)")
    sp.add_argument("--select-sql", default=None, dest="select_sql",
                    help="Materialize this SELECT as the table instead of an empty schema.")
    sp.set_defaults(func=_cmd_create_table)

    sp = with_session(sub.add_parser(
        "insert-into", help="Copy rows into a table from a SELECT/VALUES query."))
    sp.add_argument("name")
    sp.add_argument("source_sql")
    sp.set_defaults(func=_cmd_insert_into)

    with_table(with_session(sub.add_parser("count-rows", help="Row count (in-database COUNT(*))."))).set_defaults(func=_cmd_count_rows)

    sp = with_table(with_session(sub.add_parser("count-non-null", help="Non-NULL count for a column.")))
    sp.add_argument("column")
    sp.set_defaults(func=_cmd_count_non_null)

    with_table(with_session(sub.add_parser("profile", help="Profile a table."))).set_defaults(func=_cmd_profile)

    sp = with_table(with_session(sub.add_parser("outliers", help="Flag outliers in a column.")))
    sp.add_argument("--column", required=True)
    sp.set_defaults(func=_cmd_outliers)

    sp = with_table(with_session(sub.add_parser("associate", help="Test association between two columns.")))
    sp.add_argument("col_a")
    sp.add_argument("col_b")
    sp.set_defaults(func=_cmd_associate)

    with_table(with_session(sub.add_parser("assoc-matrix", help="Pairwise association matrix."))).set_defaults(func=_cmd_assoc_matrix)

    # --- feature computation ---
    sp = with_table(with_session(sub.add_parser(
        "combine-columns", help="Feature from an arithmetic op on two columns.")))
    sp.add_argument("col_a")
    sp.add_argument("col_b")
    sp.add_argument("--op", required=True, help="add|subtract|multiply|divide|ratio")
    sp.add_argument("--name", default=None)
    sp.set_defaults(func=_cmd_combine_columns)

    sp = with_table(with_session(sub.add_parser(
        "transform-column", help="Feature from a math transform of one column.")))
    sp.add_argument("column")
    sp.add_argument("--func", required=True, help="log|log1p|sqrt|square|reciprocal|abs|zscore")
    sp.add_argument("--name", default=None)
    sp.set_defaults(func=_cmd_transform_column)

    sp = with_table(with_session(sub.add_parser(
        "bin-column", help="Discretise a numeric column into ordinal bins.")))
    sp.add_argument("column")
    sp.add_argument("--n-bins", type=int, default=4, dest="n_bins")
    sp.add_argument("--strategy", default="quantile", help="quantile|uniform")
    sp.add_argument("--name", default=None)
    sp.set_defaults(func=_cmd_bin_column)

    sp = with_table(with_session(sub.add_parser(
        "expand-datetime", help="Expand a datetime column into calendar features.")))
    sp.add_argument("column")
    sp.add_argument("--parts", nargs="+", default=None,
                    help="e.g. year month dayofweek is_weekend")
    sp.set_defaults(func=_cmd_expand_datetime)

    sp = with_table(with_session(sub.add_parser(
        "group-aggregate", help="Per-group stat of a value, broadcast to rows.")))
    sp.add_argument("group_by")
    sp.add_argument("value")
    sp.add_argument("--agg", default="mean", help="mean|sum|min|max|std|median|count")
    sp.add_argument("--name", default=None)
    sp.add_argument("--add-deviation", action="store_true", dest="add_deviation")
    sp.set_defaults(func=_cmd_group_aggregate)

    sp = with_table(with_session(sub.add_parser(
        "row-aggregate", help="Row-wise aggregate across several columns.")))
    sp.add_argument("columns", nargs="+")
    sp.add_argument("--agg", default="sum", help="mean|sum|min|max|std|median|count")
    sp.add_argument("--name", default=None)
    sp.set_defaults(func=_cmd_row_aggregate)

    sp = with_table(with_session(sub.add_parser(
        "normalize-fractions", help="Turn count columns into per-row fractions of their total.")))
    sp.add_argument("columns", nargs="+")
    sp.add_argument("--suffix", default="_frac")
    sp.set_defaults(func=_cmd_normalize_fractions)

    sp = with_table(with_session(sub.add_parser(
        "compute-feature", help="Feature from a custom SQL scalar expression (in-database).")))
    sp.add_argument("name")
    sp.add_argument("expression", help="e.g. 'mass / NULLIF(volume, 0)'")
    sp.set_defaults(func=_cmd_compute_feature)

    sp = with_table(with_session(sub.add_parser("cluster", help="Cluster rows (k-means).")))
    sp.add_argument("--n-clusters", type=int, default=None, dest="n_clusters")
    sp.set_defaults(func=_cmd_cluster)

    with_table(with_session(sub.add_parser("profile-clusters", help="Characterize clusters."))).set_defaults(func=_cmd_profile_clusters)

    sp = with_table(with_session(sub.add_parser("reduce", help="Dimensionality reduction.")))
    sp.add_argument("--method", default="pca")
    sp.add_argument("--n-components", type=int, default=2, dest="n_components")
    sp.set_defaults(func=_cmd_reduce)

    for verb, task in (("train-classifier", "classification"), ("train-regressor", "regression")):
        sp = with_table(with_session(sub.add_parser(verb, help=f"Train a {task} model.")))
        sp.add_argument("target")
        sp.add_argument("--name", default=None)
        sp.add_argument(
            "--backend", default="gbt", choices=("gbt", "tabicl"),
            help="Estimator backend: gbt (gradient-boosted trees, default) or "
                 "tabicl (TabICL v2 foundation model; needs the 'tabicl' extra).",
        )
        sp.set_defaults(func=_cmd_train(task))

    for verb, fn in (("evaluate", _cmd_evaluate), ("importance", _cmd_importance)):
        sp = with_table(with_session(sub.add_parser(verb, help=f"{verb} a trained model.")))
        sp.add_argument("--model", required=True)
        sp.set_defaults(func=fn)

    sp = with_table(with_session(sub.add_parser("predict", help="Write model predictions back as a column.")))
    sp.add_argument("--model", required=True)
    sp.add_argument("--column", default=None)
    sp.set_defaults(func=_cmd_predict)

    sp = with_table(with_session(sub.add_parser("explain", help="Explain one prediction with SHAP.")))
    sp.add_argument("--model", required=True)
    sp.add_argument("--row", type=int, default=0, help="0-based table row to explain.")
    sp.set_defaults(func=_cmd_explain)

    for verb, fn in (("decompose", _cmd_decompose), ("forecast", _cmd_forecast)):
        sp = with_table(with_session(sub.add_parser(verb, help=f"Time series {verb}.")))
        sp.add_argument("--time", required=True)
        sp.add_argument("--value", required=True)
        if verb == "forecast":
            sp.add_argument("--horizon", type=int, default=10)
        sp.set_defaults(func=fn)

    sp = with_table(with_session(sub.add_parser("changepoints", help="Detect shifts in a time series (ruptures).")))
    sp.add_argument("--time", required=True)
    sp.add_argument("--value", required=True)
    sp.add_argument("--penalty", type=float, default=10.0)
    sp.set_defaults(func=_cmd_changepoints)

    sp = with_table(with_session(sub.add_parser("explain-metric", help="Rank drivers + segment rules for a metric.")))
    sp.add_argument("target")
    sp.add_argument("--max-depth", type=int, default=3, dest="max_depth")
    sp.set_defaults(func=_cmd_explain_metric)

    sp = with_table(with_session(sub.add_parser("market-basket", help="Association-rule mining (mlxtend).")))
    sp.add_argument("--transaction", required=True)
    sp.add_argument("--item", required=True)
    sp.add_argument("--min-support", type=float, default=0.01, dest="min_support")
    sp.add_argument("--min-confidence", type=float, default=0.2, dest="min_confidence")
    sp.add_argument("--max-rules", type=int, default=50, dest="max_rules")
    sp.set_defaults(func=_cmd_market_basket)

    sp = with_table(with_session(sub.add_parser("causal", help="Estimate a causal effect (DoWhy).")))
    sp.add_argument("--treatment", required=True)
    sp.add_argument("--outcome", required=True)
    sp.add_argument("--confounders", default=None, help="Comma-separated columns (default: all other features).")
    sp.set_defaults(func=_cmd_causal)

    sp = with_table(with_session(sub.add_parser("rfm", help="RFM quintile segmentation.")))
    sp.add_argument("--customer", required=True)
    sp.add_argument("--date", required=True)
    sp.add_argument("--monetary", required=True)
    sp.set_defaults(func=_cmd_rfm)

    sp = with_table(with_session(sub.add_parser("retention", help="Monthly retention cohorts.")))
    sp.add_argument("--customer", required=True)
    sp.add_argument("--date", required=True)
    sp.set_defaults(func=_cmd_retention)

    sp = with_table(with_session(sub.add_parser("compare-periods", help="Compare a metric before/after a split.")))
    sp.add_argument("--time", required=True)
    sp.add_argument("--value", required=True)
    sp.add_argument("--split", default=None, help="ISO date to split on (default: median timestamp).")
    sp.set_defaults(func=_cmd_compare_periods)

    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        _print(args.func(args))
        return 0
    except Exception as exc:  # agents parse the error as JSON too
        _print({"error": type(exc).__name__, "message": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
