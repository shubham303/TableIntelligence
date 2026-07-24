"""Tests for multi-table workspaces: loading, FK detection, and joins.

Uses the shared ``linked_session`` fixture (orders → customers + products).

Mirrors: src/tabint/analysis/service/workspace.py
"""
import shutil

import pytest

from tabint import Session


# --------------------------------------------------------------------------- #
# multi-table loading
# --------------------------------------------------------------------------- #

def test_load_multiple_tables(linked_session):
    assert set(linked_session.tables) == {"orders", "customers", "products"}


def test_single_table_still_works(tmp_path):
    from tests.conftest import copy_fixture
    dst = copy_fixture("employees.csv", tmp_path)
    s = Session.load(str(dst))
    assert s.tables == ["employees"]
    assert s.profile().summary  # flat convenience API works


def test_add_table_after_load(tmp_path):
    from tests.conftest import copy_fixture
    e = copy_fixture("employees.csv", tmp_path)
    p = copy_fixture("products.csv", tmp_path)
    s = Session.load(str(e))
    s.add_table(str(p))
    assert set(s.tables) == {"employees", "products"}


def test_table_handle_runs_analytics(linked_session):
    r = linked_session.table("customers").profile()
    assert "customer_id" in r.values


# --------------------------------------------------------------------------- #
# foreign-key detection
# --------------------------------------------------------------------------- #

def test_detects_foreign_keys(linked_session):
    graph = linked_session.relationships()
    edges = {
        (r.child_table, r.child_column, r.parent_table, r.parent_column)
        for r in graph.relationships
    }
    assert ("orders", "customer_id", "customers", "customer_id") in edges
    assert ("orders", "product_id", "products", "product_id") in edges


def test_relationship_coverage_and_name_match(linked_session):
    graph = linked_session.relationships()
    rel = next(r for r in graph.relationships if r.child_column == "customer_id")
    assert rel.coverage == 1.0
    assert rel.name_match is True


def test_neighbors(linked_session):
    graph = linked_session.relationships()
    assert graph.neighbors("orders") == {"customers", "products"}
    assert graph.neighbors("customers") == {"orders"}


def test_single_table_has_no_relationships(tmp_path):
    from tests.conftest import copy_fixture
    dst = copy_fixture("employees.csv", tmp_path)
    s = Session.load(str(dst))
    graph = s.relationships()
    assert graph.relationships == []
    assert "employees" in graph.tables


# --------------------------------------------------------------------------- #
# join → new table
# --------------------------------------------------------------------------- #

def test_join_creates_new_table(linked_session):
    joined = linked_session.join(["orders", "customers"], name="oc")
    assert joined.name == "oc"
    assert "oc" in linked_session.tables


def test_join_row_count_matches_left(linked_session):
    joined = linked_session.join(["orders", "customers"], how="left")
    assert len(joined.get_frame()) == len(linked_session.table("orders").get_frame())


def test_join_columns_disambiguated(linked_session):
    joined = linked_session.join(["orders", "customers"])
    cols = list(joined.get_frame().columns)
    assert "order_total" in cols        # from orders
    assert "tier" in cols               # from customers
    assert "customers_customer_id" in cols  # duplicated key gets prefixed


def test_analytics_run_on_joined_table(linked_session):
    joined = linked_session.join(["orders", "customers", "products"], name="enriched")
    # a single-table operation on a joined table
    r = joined.analyze_association("order_total", "tier")
    assert r.method in {"welch_t_test", "anova", "mann_whitney", "kruskal_wallis"}


def test_join_without_fk_path_raises(tmp_path):
    from tests.conftest import copy_fixture
    e = copy_fixture("employees.csv", tmp_path)
    p = copy_fixture("products.csv", tmp_path)
    s = Session.load([str(e), str(p)])
    with pytest.raises(ValueError):
        s.join(["employees", "products"])


def test_create_table_from_sql(linked_session):
    t = linked_session.create_table(
        "big_orders",
        select_sql="SELECT * FROM orders WHERE order_total > 500",
    )
    assert "big_orders" in linked_session.tables
    assert len(t.get_frame()) <= len(linked_session.table("orders").get_frame())


def test_create_table_from_schema_then_insert(linked_session):
    t = linked_session.create_table(
        "clean_orders",
        columns=[("order_id", "VARCHAR"), ("total", "DECIMAL(10,2)")],
    )
    assert list(t.get_frame().columns) == ["order_id", "total"]
    assert len(t.get_frame()) == 0

    inserted = linked_session.insert_into(
        "clean_orders", "SELECT order_id, CAST(order_total AS DECIMAL(10,2)) FROM orders"
    )
    assert inserted == len(linked_session.table("orders").get_frame())
    assert len(linked_session.table("clean_orders").get_frame()) == inserted

    # A second insert appends and _ti_row keeps ordering stable for analytics.
    linked_session.insert_into("clean_orders", "VALUES ('X9999', 1.00)")
    assert len(linked_session.table("clean_orders").get_frame()) == inserted + 1


def test_create_table_rejects_bad_type(linked_session):
    with pytest.raises(ValueError):
        linked_session.create_table("evil", columns=[("x", "VARCHAR); DROP TABLE orders;--")])


def test_create_table_requires_exactly_one_mode(linked_session):
    with pytest.raises(ValueError):
        linked_session.create_table("neither")
    with pytest.raises(ValueError):
        linked_session.create_table("both", columns=[("x", "INT")], select_sql="SELECT 1")


# --------------------------------------------------------------------------- #
# derived-column registry: written-back annotations must not leak into features
# --------------------------------------------------------------------------- #

def test_derived_columns_excluded_from_features(linked_session):
    from tabint.analysis.service import _prep

    orders = linked_session.table("orders")
    before_num, before_cat = _prep.feature_columns(orders)

    # A written-back annotation column must be recorded as derived...
    orders.write_back_column("flagged", [True] * len(orders.get_frame()))
    assert "flagged" in orders.derived_columns()

    # ...and therefore never appear as a feature.
    after_num, after_cat = _prep.feature_columns(orders)
    assert "flagged" not in after_num + after_cat
    assert (after_num, after_cat) == (before_num, before_cat)


def test_write_back_feature_true_stays_a_feature(linked_session):
    from tabint.analysis.service import _prep

    orders = linked_session.table("orders")
    n = len(orders.get_frame())
    orders.write_back_column("component_0", [i * 0.1 for i in range(n)], feature=True)
    assert "component_0" not in orders.derived_columns()
    num, cat = _prep.feature_columns(orders)
    assert "component_0" in num


def test_derived_registry_survives_reopen(tmp_path):
    from tabint.analysis.service import _prep
    from tabint.analysis.service.workspace import Workspace
    from tests.conftest import copy_fixture

    db = str(tmp_path / "ws.duckdb")
    src = copy_fixture("orders.csv", tmp_path)

    ws = Workspace.create([str(src)], db_path=db)
    t = ws.table("orders")
    t.write_back_column("anomaly", [False] * len(t.get_frame()))
    assert "anomaly" in t.derived_columns()
    ws.close()

    reopened = Workspace(db_path=db)
    rt = reopened.table("orders")
    assert "anomaly" in rt.derived_columns()
    num, cat = _prep.feature_columns(rt)
    assert "anomaly" not in num + cat
    reopened.close()
