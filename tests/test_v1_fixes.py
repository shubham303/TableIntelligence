"""Regression tests for the V1-surface verification findings."""
import json
import math

import numpy as np
import pandas as pd
import pytest

from tabular import persistence
from tabular._serialize import jsonable
from tabular.cli import main


def _csv(tmp_path, name, df):
    p = tmp_path / name
    df.to_csv(p, index=False)
    return str(p)


def _run(capsys, argv):
    code = main(argv)
    return code, json.loads(capsys.readouterr().out)


# --- #1/#5: association of a column with itself -> clear error ------------- #

def test_associate_same_column_clear_error(tmp_path, capsys):
    base = str(tmp_path)
    _, load = _run(capsys, ["--base", base, "load", _csv(tmp_path, "d.csv",
                   pd.DataFrame({"x": np.arange(30.0), "y": np.arange(30.0)}))])
    key = load["session_key"]
    code, data = _run(capsys, ["--base", base, "associate", "x", "x", "--session", key, "--table", "d"])
    assert code == 1
    assert data["error"] == "ValueError"
    assert "itself" in data["message"]


# --- #2: Infinity is coerced to null (valid JSON) ------------------------- #

def test_jsonable_handles_infinity():
    out = jsonable({"a": float("inf"), "b": float("-inf"), "c": float("nan"), "d": 1.5})
    assert out == {"a": None, "b": None, "c": None, "d": 1.5}
    json.loads(json.dumps(out))  # strict parse succeeds


def test_cli_sql_infinity_is_valid_json(tmp_path, capsys):
    base = str(tmp_path)
    _, load = _run(capsys, ["--base", base, "load", _csv(tmp_path, "d.csv", pd.DataFrame({"x": [1, 2]}))])
    key = load["session_key"]
    _, data = _run(capsys, ["--base", base, "sql", "SELECT 1.0/0.0 AS x", "--session", key])
    assert data["rows"][0]["x"] is None          # +inf -> null, not bareword Infinity


# --- #3: corrupt meta.json doesn't poison later writes -------------------- #

def test_corrupt_meta_survives(tmp_path):
    s = persistence.create_session([_csv(tmp_path, "d.csv",
                                    pd.DataFrame({"x": range(20), "y": [0, 1] * 10}))], base=tmp_path)
    (persistence.session_dir(s.id, base=tmp_path) / "meta.json").write_text("{ this is corrupt")
    # a subsequent train + save_model must still succeed despite the bad meta
    model = s.table("d").train_classifier("y", name="m")
    persistence.save_model(s, "d", "m", model)     # calls _write_meta; must not raise
    meta = json.loads((persistence.session_dir(s.id, base=tmp_path) / "meta.json").read_text())
    assert "m" in meta["models"]["d"]


# --- #4: non-numeric regression target -> clear error --------------------- #

def test_train_regressor_non_numeric_target(tmp_path, capsys):
    base = str(tmp_path)
    df = pd.DataFrame({"x": np.arange(30.0), "label": ["a", "b", "c"] * 10})
    _, load = _run(capsys, ["--base", base, "load", _csv(tmp_path, "d.csv", df)])
    key = load["session_key"]
    code, data = _run(capsys, ["--base", base, "train-regressor", "label", "--session", key, "--table", "d"])
    assert code == 1
    assert "numeric" in data["message"].lower()


# --- #6: continuous float on a small table classifies as continuous ------- #

def test_small_table_float_is_continuous(tmp_path):
    df = pd.DataFrame({"grp": ["a", "b"] * 6, "measure": [float(i) + 0.5 for i in range(12)]})
    s = persistence.create_session([_csv(tmp_path, "d.csv", df)], base=tmp_path)
    r = s.table("d").analyze_association("grp", "measure")
    # 'measure' must be treated as continuous -> a group test, not chi-square
    assert r.method in {"welch_t_test", "anova", "mann_whitney", "kruskal_wallis"}


# --- #7: explain_prediction reachable from the CLI (and MCP) -------------- #

def test_cli_explain_prediction(tmp_path, capsys):
    base = str(tmp_path)
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"x1": rng.normal(size=60), "x2": rng.normal(size=60),
                       "y": rng.integers(0, 2, 60)})
    _, load = _run(capsys, ["--base", base, "load", _csv(tmp_path, "d.csv", df)])
    key = load["session_key"]
    _run(capsys, ["--base", base, "train-classifier", "y", "--session", key, "--table", "d", "--name", "m"])
    code, data = _run(capsys, ["--base", base, "explain", "--session", key, "--table", "d", "--model", "m", "--row", "0"])
    assert code == 0
    assert data["method"] == "shap"
    assert "contributions" in data["values"]


def test_mcp_exposes_explain_prediction():
    from tabular import mcp_server as M
    assert hasattr(M, "explain_prediction")
