"""Command-line surface — lets a terminal agent (e.g. Claude Code) drive the core.

Every command prints a JSON object to stdout so an agent can parse the result.
State lives in on-disk sessions (see tabular.persistence): ``tabular load`` mints a
session key; pass ``--session <key>`` to every later command to keep working on the
same data. Analytics operate on ONE table (``--table``) — an uploaded table or one
produced by ``tabular join``.

Examples::

    tabular load orders.csv customers.csv          # -> {"session_key": "s_ab12", ...}
    tabular relationships --session s_ab12
    tabular join orders customers --session s_ab12 --name enriched
    tabular associate order_total tier --session s_ab12 --table enriched
    tabular train-classifier is_churned --session s_ab12 --table customers --name churn
    tabular evaluate --session s_ab12 --table customers --model churn
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import persistence
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


def _cmd_profile(args) -> dict:
    return result_dict(_open(args).table(args.table).profile())


def _cmd_outliers(args) -> dict:
    return result_dict(_open(args).table(args.table).detect_outliers(args.column))


def _cmd_associate(args) -> dict:
    return result_dict(_open(args).table(args.table).analyze_association(args.col_a, args.col_b))


def _cmd_assoc_matrix(args) -> dict:
    return result_dict(_open(args).table(args.table).association_matrix())


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
            args.target, name=model_name
        )
        persistence.save_model(s, args.table, model_name, model)
        return {"model_name": model_name, "table": args.table, "target": args.target,
                "task": task, "features": model._feature_names}
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


# --------------------------------------------------------------------------- #
# parser
# --------------------------------------------------------------------------- #

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tabular", description="Deterministic single-table data analysis.")
    p.add_argument("--base", default=".", help="Root dir holding .tableint/sessions (default: cwd).")
    sub = p.add_subparsers(dest="command", required=True)

    def with_session(sp):
        sp.add_argument("--session", required=True, help="Session key from `tabular load`.")
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

    with_session(sub.add_parser("relationships", help="Detect the FK graph.")).set_defaults(func=_cmd_relationships)

    sp = with_session(sub.add_parser("join", help="Join tables along FKs into a new table."))
    sp.add_argument("tables", nargs="+")
    sp.add_argument("--name", default=None)
    sp.add_argument("--how", default="left")
    sp.set_defaults(func=_cmd_join)

    sp = with_session(sub.add_parser("sql", help="Run SQL over the session."))
    sp.add_argument("query")
    sp.add_argument("--limit", type=int, default=1000)
    sp.set_defaults(func=_cmd_sql)

    with_table(with_session(sub.add_parser("profile", help="Profile a table."))).set_defaults(func=_cmd_profile)

    sp = with_table(with_session(sub.add_parser("outliers", help="Flag outliers in a column.")))
    sp.add_argument("--column", required=True)
    sp.set_defaults(func=_cmd_outliers)

    sp = with_table(with_session(sub.add_parser("associate", help="Test association between two columns.")))
    sp.add_argument("col_a")
    sp.add_argument("col_b")
    sp.set_defaults(func=_cmd_associate)

    with_table(with_session(sub.add_parser("assoc-matrix", help="Pairwise association matrix."))).set_defaults(func=_cmd_assoc_matrix)

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
