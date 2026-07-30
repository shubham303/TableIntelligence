"""Tests for on-disk session persistence (the CLI/MCP state layer).

Real filesystem + real DuckDB (only the base dir is redirected via tmp_path).

Mirrors: src/tabint/analysis/db/persistence.py
"""
import json

import numpy as np
import pandas as pd
import pytest

from tabint.analysis.db import persistence
from tests.unit.factory import numeric_frame


def test_create_returns_session_key(tmp_path, csv_writer):
    s = persistence.create_session([csv_writer(numeric_frame(), "churn.csv")], base=tmp_path)
    assert s.id and s.id.startswith("s_")
    assert s.tables == ["churn"]
    assert (persistence.session_dir(s.id, base=tmp_path) / "data.duckdb").exists()


def test_write_back_column_persists_across_open(tmp_path, csv_writer):
    s = persistence.create_session([csv_writer(numeric_frame(), "churn.csv")], base=tmp_path)
    sid = s.id
    t = s.table("churn")
    t.classify_categorical_as_nominal()  # mock the LLM step (y is low-card categorical)
    t.cluster(n_clusters=2)               # writes a 'cluster' column
    s.close()                             # release the DB file

    reopened = persistence.open_session(sid, base=tmp_path)
    assert "cluster" in reopened.table("churn").get_frame().columns


def test_model_persists_and_evaluates_after_reopen(tmp_path, csv_writer):
    # Simulates the CLI flow: train in one process, evaluate in the next.
    s = persistence.create_session([csv_writer(numeric_frame(), "churn.csv")], base=tmp_path)
    sid = s.id
    model = s.table("churn").train_classifier("y", name="m1")
    persistence.save_model(s, "churn", "m1", model)
    s.close()

    reopened = persistence.open_session(sid, base=tmp_path)
    assert "m1" in reopened.table("churn").models      # model restored
    result = reopened.table("churn").evaluate("m1")     # usable after reopen
    assert 0.0 <= result.values["accuracy"] <= 1.0


def test_multi_table_session_persists(tmp_path, csv_writer):
    cust = csv_writer(pd.DataFrame({"customer_id": [1, 2, 3], "name": list("xyz")}), "customers.csv")
    orders = csv_writer(
        pd.DataFrame({"order_id": [10, 11, 12], "customer_id": [1, 2, 1]}), "orders.csv",
    )
    s = persistence.create_session([cust, orders], base=tmp_path)
    sid = s.id
    s.close()

    reopened = persistence.open_session(sid, base=tmp_path)
    assert set(reopened.tables) == {"customers", "orders"}
    edges = {(r.child_table, r.parent_table) for r in reopened.relationships().relationships}
    assert ("orders", "customers") in edges


def test_list_sessions(tmp_path, csv_writer):
    s1 = persistence.create_session([csv_writer(numeric_frame(), "a.csv")], base=tmp_path)
    s2 = persistence.create_session([csv_writer(numeric_frame(), "b.csv")], base=tmp_path)
    keys = persistence.list_sessions(base=tmp_path)
    assert s1.id in keys and s2.id in keys


def test_open_unknown_session_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        persistence.open_session("s_deadbeef", base=tmp_path)


def test_meta_json_records_tables_and_models(tmp_path, csv_writer):
    s = persistence.create_session([csv_writer(numeric_frame(), "churn.csv")], base=tmp_path)
    persistence.save_model(s, "churn", "m1", s.table("churn").train_classifier("y", name="m1"))
    meta = json.loads((persistence.session_dir(s.id, base=tmp_path) / "meta.json").read_text())
    assert meta["session_id"] == s.id
    assert meta["tables"] == ["churn"]
    assert "m1" in meta["models"]["churn"]
    assert "created_at" in meta


# --- #3: corrupt meta.json doesn't poison later writes (from test_v1_fixes) - #

def test_corrupt_meta_survives(tmp_path, csv_writer):
    s = persistence.create_session([csv_writer(numeric_frame(), "d.csv")], base=tmp_path)
    (persistence.session_dir(s.id, base=tmp_path) / "meta.json").write_text("{ this is corrupt")
    # a subsequent train + save_model must still succeed despite the bad meta
    model = s.table("d").train_classifier("y", name="m")
    persistence.save_model(s, "d", "m", model)     # calls _write_meta; must not raise
    meta = json.loads((persistence.session_dir(s.id, base=tmp_path) / "meta.json").read_text())
    assert "m" in meta["models"]["d"]
