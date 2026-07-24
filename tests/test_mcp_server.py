"""Tests for the MCP server — tool logic (direct calls) and protocol wiring."""
import asyncio
import shutil

import pytest

from tabint.analysis import tools as M
from tabint.shared import server as _srv


@pytest.fixture(autouse=True)
def isolate(tmp_path):
    """Point the server at a temp session root and clear the live registry."""
    _srv._BASE = str(tmp_path)
    _srv._SESSIONS.clear()
    yield
    _srv._SESSIONS.clear()


def _fixtures(tmp_path, *names):
    out = []
    for n in names:
        dst = tmp_path / n
        shutil.copy(f"tests/fixtures/{n}", dst)
        out.append(str(dst))
    return out


# --- tool logic (direct calls) -------------------------------------------- #

def test_create_session_returns_key_and_graph(tmp_path):
    r = M.create_session(_fixtures(tmp_path, "orders.csv", "customers.csv", "products.csv"))
    assert r["session_key"].startswith("s_")
    assert set(r["tables"]) == {"orders", "customers", "products"}
    edges = {(e["child_table"], e["parent_table"]) for e in r["relationships"]["relationships"]}
    assert ("orders", "customers") in edges and ("orders", "products") in edges


def test_analytics_by_session_key(tmp_path):
    key = M.create_session(_fixtures(tmp_path, "customers.csv"))["session_key"]
    assert M.profile(key, "customers")["values"]["age"]["type"] == "continuous"
    assert M.analyze_association(key, "customers", "age", "total_spend")["method"] in {"pearson", "spearman"}
    assert M.cluster(key, "customers", 3)["values"]["n_clusters"] == 3


def test_feature_computation_tools_build_model_eligible_columns(tmp_path):
    key = M.create_session(_fixtures(tmp_path, "employees.csv"))["session_key"]
    r = M.combine_columns(key, "employees", "salary", "years_at_company", "divide", name="rate")
    assert r["values"]["column"] == "rate"
    M.group_aggregate(key, "employees", "department", "salary", "mean", add_deviation=True)
    cols = M.run_sql(key, "SELECT * FROM employees LIMIT 1")["rows"][0].keys()
    assert {"rate", "salary_mean_by_department", "salary_dev_from_department"} <= set(cols)
    # Engineered columns are features, so training picks them up (not excluded).
    fi = M.train_regressor(key, "employees", "salary", name="m")
    assert fi is not None


def test_train_evaluate_persist_across_cache_eviction(tmp_path):
    key = M.create_session(_fixtures(tmp_path, "loan_applications.csv"))["session_key"]
    M.train_classifier(key, "loan_applications", "is_approved", name="m")
    _srv._SESSIONS.clear()                    # simulate server restart / eviction
    r = M.evaluate(key, "loan_applications", "m")   # reopened from disk by key
    assert 0.0 <= r["values"]["accuracy"] <= 1.0


def test_join_then_analyze(tmp_path):
    key = M.create_session(_fixtures(tmp_path, "orders.csv", "customers.csv"))["session_key"]
    j = M.join(key, ["orders", "customers"], name="enriched")
    assert j["table"] == "enriched" and j["n_rows"] == 80
    r = M.analyze_association(key, "enriched", "order_total", "tier")
    assert r["method"] in {"welch_t_test", "anova", "mann_whitney", "kruskal_wallis"}


def test_unknown_session_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        M.profile("s_deadbeef", "x")


def test_scratchpad_requires_live_session(tmp_path, monkeypatch):
    from tabint.shared import scratchpad

    monkeypatch.setattr(scratchpad, "_DIR", tmp_path / ".tableintelligence")
    # No active session for this key → every scratchpad op must raise.
    with pytest.raises(FileNotFoundError):
        M.scratchpad_add("s_deadbeef", "note")
    with pytest.raises(FileNotFoundError):
        M.scratchpad_read("s_deadbeef")
    with pytest.raises(FileNotFoundError):
        M.scratchpad_search("s_deadbeef", "q")


def test_scratchpad_add_read_with_live_session(tmp_path, monkeypatch):
    from tabint.shared import scratchpad

    monkeypatch.setattr(scratchpad, "_DIR", tmp_path / ".tableintelligence")
    key = M.create_session(_fixtures(tmp_path, "customers.csv"))["session_key"]
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
