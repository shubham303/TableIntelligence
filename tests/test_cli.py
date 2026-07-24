"""Tests for the terminal CLI — JSON output and the process-per-call session chain."""
import json
import shutil

import pytest

from tabint.app.cli import main


def _run(capsys, argv) -> tuple[int, object]:
    code = main(argv)
    out = capsys.readouterr().out
    return code, json.loads(out)


def _fixtures(tmp_path, *names):
    out = []
    for n in names:
        dst = tmp_path / n
        shutil.copy(f"tests/fixtures/{n}", dst)
        out.append(str(dst))
    return out


def test_load_prints_session_key(tmp_path, capsys):
    code, data = _run(capsys, ["--base", str(tmp_path), "load", *_fixtures(tmp_path, "customers.csv")])
    assert code == 0
    assert data["session_key"].startswith("s_")
    assert data["tables"] == ["customers"]


def test_full_chain_across_calls(tmp_path, capsys):
    base = str(tmp_path)
    files = _fixtures(tmp_path, "orders.csv", "customers.csv", "products.csv")
    _, load = _run(capsys, ["--base", base, "load", *files])
    key = load["session_key"]

    _, rel = _run(capsys, ["--base", base, "relationships", "--session", key])
    edges = {(r["child_table"], r["parent_table"]) for r in rel["relationships"]}
    assert ("orders", "customers") in edges

    _, joined = _run(capsys, ["--base", base, "join", "orders", "customers", "--session", key, "--name", "enriched"])
    assert joined["table"] == "enriched" and joined["n_rows"] == 80

    # train in one "process", evaluate in the next — model restored from disk
    _, trained = _run(capsys, ["--base", base, "train-classifier", "is_churned",
                               "--session", key, "--table", "customers", "--name", "churn"])
    assert trained["model_name"] == "churn"
    _, ev = _run(capsys, ["--base", base, "evaluate", "--session", key, "--table", "customers", "--model", "churn"])
    assert 0.0 <= ev["values"]["accuracy"] <= 1.0


def test_associate_picks_test(tmp_path, capsys):
    base = str(tmp_path)
    _, load = _run(capsys, ["--base", base, "load", *_fixtures(tmp_path, "employees.csv")])
    key = load["session_key"]
    _, r = _run(capsys, ["--base", base, "associate", "department", "salary", "--session", key, "--table", "employees"])
    assert r["method"] in {"welch_t_test", "anova", "mann_whitney", "kruskal_wallis"}


def test_error_is_json(tmp_path, capsys):
    code, data = _run(capsys, ["--base", str(tmp_path), "info", "--session", "s_nope"])
    assert code == 1
    assert data["error"] == "FileNotFoundError"


def test_sql_query(tmp_path, capsys):
    base = str(tmp_path)
    _, load = _run(capsys, ["--base", base, "load", *_fixtures(tmp_path, "customers.csv")])
    key = load["session_key"]
    _, r = _run(capsys, ["--base", base, "sql", "SELECT COUNT(*) AS n FROM customers", "--session", key])
    assert r["rows"][0]["n"] == 30
