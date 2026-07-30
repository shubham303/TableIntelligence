"""Tests for the MCP server — tool logic (direct calls) and protocol wiring.

The autouse ``_isolate_sessions`` / ``_isolate_scratchpad`` fixtures from the
integration conftest redirect the server root and scratchpad dir into tmp_path,
so this file no longer needs its own ``isolate`` fixture.

Mirrors: src/tabint/analysis/tools.py, src/tabint/shared/server.py
"""
import asyncio

import pytest

from tabint.analysis import tools as M
from tests.conftest import copy_fixtures


# --- tool logic (direct calls) -------------------------------------------- #

def test_create_session_returns_key_and_graph(tmp_path):
    r = M.create_session(copy_fixtures(tmp_path, "orders.csv", "customers.csv", "products.csv"))
    assert r["session_key"].startswith("s_")
    assert set(r["tables"]) == {"orders", "customers", "products"}
    edges = {(e["child_table"], e["parent_table"]) for e in r["relationships"]["relationships"]}
    assert ("orders", "customers") in edges and ("orders", "products") in edges


def test_analytics_by_session_key(tmp_path):
    key = M.create_session(copy_fixtures(tmp_path, "customers.csv"))["session_key"]
    M.classify_as_nominal(key, "customers")  # mock the LLM classification step
    assert M.profile(key, "customers")["values"]["age"]["type"] == "continuous"
    assert M.analyze_association(key, "customers", "age", "total_spend")["method"] in {"pearson", "spearman"}
    assert M.cluster(key, "customers", 3)["values"]["n_clusters"] == 3


def test_feature_computation_tools_build_model_eligible_columns(tmp_path):
    key = M.create_session(copy_fixtures(tmp_path, "employees.csv"))["session_key"]
    M.classify_as_nominal(key, "employees")  # mock the LLM classification step
    r = M.combine_columns(key, "employees", "salary", "years_at_company", "divide", name="rate")
    assert r["values"]["column"] == "rate"
    M.group_aggregate(key, "employees", "department", "salary", "mean", add_deviation=True)
    cols = M.run_sql(key, "SELECT * FROM employees LIMIT 1")["rows"][0].keys()
    assert {"rate", "salary_mean_by_department", "salary_dev_from_department"} <= set(cols)
    # New derived categorical columns appear unclassified; re-run the mock step.
    M.classify_as_nominal(key, "employees")
    # Engineered columns are features, so training picks them up (not excluded).
    fi = M.train_regressor(key, "employees", "salary", name="m")
    assert fi is not None


def test_train_evaluate_persist_across_cache_eviction(tmp_path):
    key = M.create_session(copy_fixtures(tmp_path, "loan_applications.csv"))["session_key"]
    M.classify_as_nominal(key, "loan_applications")  # mock the LLM classification step
    M.train_classifier(key, "loan_applications", "is_approved", name="m")
    from tabint.shared import server
    server._SESSIONS.clear()                    # simulate server restart / eviction
    r = M.evaluate(key, "loan_applications", "m")   # reopened from disk by key
    assert 0.0 <= r["values"]["accuracy"] <= 1.0


def test_join_then_analyze(tmp_path):
    key = M.create_session(copy_fixtures(tmp_path, "orders.csv", "customers.csv"))["session_key"]
    j = M.join(key, ["orders", "customers"], name="enriched")
    assert j["table"] == "enriched" and j["n_rows"] == 80
    M.classify_as_nominal(key, "enriched")  # mock the LLM step (tier is categorical)
    r = M.analyze_association(key, "enriched", "order_total", "tier")
    assert r["method"] in {"welch_t_test", "anova", "mann_whitney", "kruskal_wallis"}


# --- column-type classification tools ------------------------------------- #

def test_list_categorical_columns_is_a_worklist(tmp_path):
    key = M.create_session(copy_fixtures(tmp_path, "employees.csv"))["session_key"]
    r = M.list_categorical_columns(key, "employees")
    names = {c["column"] for c in r["unclassified"]}
    assert "department" in names and r["n"] == len(names)

    # Refining one column drops it off the worklist.
    M.set_column_type(key, "employees", "department", "categorical_nominal")
    r = M.list_categorical_columns(key, "employees")
    assert "department" not in {c["column"] for c in r["unclassified"]}


def test_classify_as_nominal_empties_the_worklist(tmp_path):
    key = M.create_session(copy_fixtures(tmp_path, "employees.csv"))["session_key"]
    assert M.list_categorical_columns(key, "employees")["n"] > 0
    M.classify_as_nominal(key, "employees")
    # Every categorical refined -> empty worklist.
    assert M.list_categorical_columns(key, "employees")["unclassified"] == []


def test_set_column_type_rejects_non_categorical_types(tmp_path):
    key = M.create_session(copy_fixtures(tmp_path, "employees.csv"))["session_key"]
    for bad in ("continuous", "datetime", "identifier", "categorical", "nope"):
        with pytest.raises(ValueError):
            M.set_column_type(key, "employees", "department", bad)


def test_derived_categorical_re_surfaces_on_worklist(tmp_path):
    # A new derived categorical column is unclassified and appears on the
    # worklist even after the original columns were all refined.
    key = M.create_session(copy_fixtures(tmp_path, "employees.csv"))["session_key"]
    M.classify_as_nominal(key, "employees")
    assert M.list_categorical_columns(key, "employees")["unclassified"] == []
    M.bin_column(key, "employees", "salary", n_bins=4, name="salary_band")
    worklist = {c["column"] for c in M.list_categorical_columns(key, "employees")["unclassified"]}
    assert "salary_band" in worklist


def test_unset_column_type_returns_column_to_worklist(tmp_path):
    key = M.create_session(copy_fixtures(tmp_path, "employees.csv"))["session_key"]
    M.set_column_type(key, "employees", "department", "categorical_ordinal")
    assert "department" not in {
        c["column"] for c in M.list_categorical_columns(key, "employees")["unclassified"]
    }
    M.unset_column_type(key, "employees", "department")
    assert "department" in {
        c["column"] for c in M.list_categorical_columns(key, "employees")["unclassified"]
    }


def test_unknown_session_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        M.profile("s_deadbeef", "x")


def test_scratchpad_requires_live_session(tmp_path):
    from tabint.shared import scratchpad
    # No active session for this key → every scratchpad op must raise.
    with pytest.raises(FileNotFoundError):
        M.scratchpad_add("s_deadbeef", "note")
    with pytest.raises(FileNotFoundError):
        M.scratchpad_read("s_deadbeef")
    with pytest.raises(FileNotFoundError):
        M.scratchpad_search("s_deadbeef", "q")


def test_scratchpad_add_read_with_live_session(tmp_path):
    key = M.create_session(copy_fixtures(tmp_path, "customers.csv"))["session_key"]
    M.scratchpad_add(key, "customers skew young")
    assert "customers skew young" in M.scratchpad_read(key)["text"]
    assert M.scratchpad_search(key, "SKEW")["matches"]


# --- protocol wiring ------------------------------------------------------- #

def test_protocol_lists_tools_and_calls(tmp_path):
    async def go():
        tools = await M.mcp.list_tools()
        names = {t.name for t in tools}
        # a representative spread across the families must be exposed
        assert {"create_session", "profile", "analyze_association", "cluster",
                "train_classifier", "join", "relationships", "run_sql"} <= names
        await M.mcp.call_tool("list_sessions", {})   # round-trips without error
        return len(tools)

    assert asyncio.run(go()) >= 18
