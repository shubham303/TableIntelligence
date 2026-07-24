"""Tests for the terminal CLI — JSON output and the process-per-call session chain.

Uses the shared ``cli_runner`` and ``copy_fixtures`` fixtures. Merges the CLI
regression tests from test_v1_fixes.py.

Mirrors: src/tabint/app/cli.py
"""
import numpy as np
import pandas as pd
import pytest

from tests.unit.factory import numeric_frame


# --------------------------------------------------------------------------- #
# basic load / chain
# --------------------------------------------------------------------------- #

def test_load_prints_session_key(tmp_path, cli_runner):
    from tests.conftest import copy_fixtures
    code, data = cli_runner(["--base", str(tmp_path), "load", *copy_fixtures(tmp_path, "customers.csv")])
    assert code == 0
    assert data["session_key"].startswith("s_")
    assert data["tables"] == ["customers"]


def test_full_chain_across_calls(tmp_path, cli_runner):
    from tests.conftest import copy_fixtures
    base = str(tmp_path)
    files = copy_fixtures(tmp_path, "orders.csv", "customers.csv", "products.csv")
    _, load = cli_runner(["--base", base, "load", *files])
    key = load["session_key"]

    _, rel = cli_runner(["--base", base, "relationships", "--session", key])
    edges = {(r["child_table"], r["parent_table"]) for r in rel["relationships"]}
    assert ("orders", "customers") in edges

    _, joined = cli_runner(["--base", base, "join", "orders", "customers", "--session", key, "--name", "enriched"])
    assert joined["table"] == "enriched" and joined["n_rows"] == 80

    # train in one "process", evaluate in the next — model restored from disk
    _, trained = cli_runner(["--base", base, "train-classifier", "is_churned",
                             "--session", key, "--table", "customers", "--name", "churn"])
    assert trained["model_name"] == "churn"
    _, ev = cli_runner(["--base", base, "evaluate", "--session", key, "--table", "customers", "--model", "churn"])
    assert 0.0 <= ev["values"]["accuracy"] <= 1.0


def test_associate_picks_test(tmp_path, cli_runner):
    from tests.conftest import copy_fixtures
    base = str(tmp_path)
    _, load = cli_runner(["--base", base, "load", *copy_fixtures(tmp_path, "employees.csv")])
    key = load["session_key"]
    _, r = cli_runner(["--base", base, "associate", "department", "salary", "--session", key, "--table", "employees"])
    assert r["method"] in {"welch_t_test", "anova", "mann_whitney", "kruskal_wallis"}


def test_error_is_json(tmp_path, cli_runner):
    code, data = cli_runner(["--base", str(tmp_path), "info", "--session", "s_nope"])
    assert code == 1
    assert data["error"] == "FileNotFoundError"


def test_sql_query(tmp_path, cli_runner):
    from tests.conftest import copy_fixtures
    base = str(tmp_path)
    _, load = cli_runner(["--base", base, "load", *copy_fixtures(tmp_path, "customers.csv")])
    key = load["session_key"]
    _, r = cli_runner(["--base", base, "sql", "SELECT COUNT(*) AS n FROM customers", "--session", key])
    assert r["rows"][0]["n"] == 30


# --------------------------------------------------------------------------- #
# regression cases from test_v1_fixes.py
# --------------------------------------------------------------------------- #

def test_associate_same_column_clear_error(tmp_path, cli_runner, csv_writer):
    base = str(tmp_path)
    df = pd.DataFrame({"x": np.arange(30.0), "y": np.arange(30.0)})
    _, load = cli_runner(["--base", base, "load", csv_writer(df, "d.csv")])
    key = load["session_key"]
    code, data = cli_runner(["--base", base, "associate", "x", "x", "--session", key, "--table", "d"])
    assert code == 1
    assert data["error"] == "ValueError"
    assert "itself" in data["message"]


def test_cli_sql_infinity_is_valid_json(tmp_path, cli_runner, csv_writer):
    base = str(tmp_path)
    df = pd.DataFrame({"x": [1, 2]})
    _, load = cli_runner(["--base", base, "load", csv_writer(df, "d.csv")])
    key = load["session_key"]
    _, data = cli_runner(["--base", base, "sql", "SELECT 1.0/0.0 AS x", "--session", key])
    assert data["rows"][0]["x"] is None          # +inf -> null, not bareword Infinity


def test_train_regressor_non_numeric_target(tmp_path, cli_runner, csv_writer):
    base = str(tmp_path)
    df = pd.DataFrame({"x": np.arange(30.0), "label": ["a", "b", "c"] * 10})
    _, load = cli_runner(["--base", base, "load", csv_writer(df, "d.csv")])
    key = load["session_key"]
    code, data = cli_runner(["--base", base, "train-regressor", "label", "--session", key, "--table", "d"])
    assert code == 1
    assert "numeric" in data["message"].lower()


def test_cli_explain_prediction(tmp_path, cli_runner, csv_writer):
    base = str(tmp_path)
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"x1": rng.normal(size=60), "x2": rng.normal(size=60),
                       "y": rng.integers(0, 2, 60)})
    _, load = cli_runner(["--base", base, "load", csv_writer(df, "d.csv")])
    key = load["session_key"]
    cli_runner(["--base", base, "train-classifier", "y", "--session", key, "--table", "d", "--name", "m"])
    code, data = cli_runner(["--base", base, "explain", "--session", key, "--table", "d", "--model", "m", "--row", "0"])
    assert code == 0
    assert data["method"] == "shap"
    assert "contributions" in data["values"]
