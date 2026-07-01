"""Tests for the DuckDB-backed Store."""
import shutil

import pandas as pd
import pytest

from tabular.store import Store

CUSTOMERS = "tests/fixtures/customers.csv"
EMPLOYEES = "tests/fixtures/employees.csv"


@pytest.fixture(autouse=True)
def clear_registry():
    """Reset the Store registry before each test so tests are isolated."""
    Store._registry.clear()
    yield
    Store._registry.clear()


@pytest.fixture
def store(tmp_path, monkeypatch):
    """A Store loaded from the customers fixture, using a temp dir for .tableint."""
    src = "tests/fixtures/customers.csv"
    csv = tmp_path / "customers.csv"
    shutil.copy(src, csv)
    return Store.for_csv(str(csv))


# ---------------------------------------------------------------------------
# 1. CSV load
# ---------------------------------------------------------------------------

def test_load_creates_duckdb_file(tmp_path):
    csv = tmp_path / "customers.csv"
    shutil.copy(CUSTOMERS, csv)

    Store.for_csv(str(csv))

    db_files = list((tmp_path / ".tableint" / "store").glob("*.duckdb"))
    assert len(db_files) == 1


def test_load_imports_all_rows(store):
    result = store.run_sql("SELECT COUNT(*) AS n FROM data")
    assert result["n"].iloc[0] == 30


def test_load_imports_all_columns(store):
    cols = set(store.run_sql("SELECT * FROM data LIMIT 1").columns)
    expected = {"customer_id", "name", "country", "tier", "age",
                "total_spend", "num_orders", "avg_order_value",
                "is_churned", "has_subscription"}
    assert expected == cols


def test_ti_row_not_visible_to_user(store):
    cols = set(store.run_sql("SELECT * FROM data LIMIT 1").columns)
    assert "_ti_row" not in cols


# ---------------------------------------------------------------------------
# 2. SQL queries
# ---------------------------------------------------------------------------

def test_run_sql_returns_dataframe(store):
    result = store.run_sql("SELECT * FROM data LIMIT 5")
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 5


def test_run_sql_filter(store):
    result = store.run_sql("SELECT customer_id FROM data WHERE country = 'USA'")
    assert len(result) > 0
    assert set(result.columns) == {"customer_id"}


def test_run_sql_aggregation(store):
    result = store.run_sql(
        "SELECT tier, COUNT(*) AS n FROM data GROUP BY tier ORDER BY tier"
    )
    assert "tier" in result.columns
    assert result["n"].sum() == 30


# ---------------------------------------------------------------------------
# 3. write_back_column
# ---------------------------------------------------------------------------

def test_write_back_adds_new_column(store):
    store.write_back_column("score", list(range(30)))
    cols = set(store.run_sql("SELECT * FROM data LIMIT 1").columns)
    assert "score" in cols


def test_write_back_values_are_correct(store):
    values = list(range(30))
    store.write_back_column("score", values)
    result = store.run_sql("SELECT score FROM data")
    assert list(result["score"]) == values


def test_write_back_overwrites_existing_column(store):
    store.write_back_column("score", list(range(30)))
    store.write_back_column("score", list(range(100, 130)))
    result = store.run_sql("SELECT score FROM data")
    assert list(result["score"]) == list(range(100, 130))


def test_write_back_preserves_other_columns(store):
    original_ids = list(store.run_sql("SELECT customer_id FROM data")["customer_id"])
    store.write_back_column("score", list(range(30)))
    ids_after = list(store.run_sql("SELECT customer_id FROM data")["customer_id"])
    assert original_ids == ids_after


def test_write_back_multiple_columns(store):
    store.write_back_column("score", list(range(30)))
    store.write_back_column("rank", list(range(1, 31)))
    result = store.run_sql("SELECT score, rank FROM data")
    assert list(result["score"]) == list(range(30))
    assert list(result["rank"]) == list(range(1, 31))
