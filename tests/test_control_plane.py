"""Tests for the layered control plane (repository → service) on DuckDB."""
from __future__ import annotations

import pytest

from tabint_control import create_provider, security
from tabint_control.services import AdminService, EntitlementService


@pytest.fixture()
def provider(tmp_path):
    p = create_provider(str(tmp_path / "control.duckdb"))
    p.init_schema()
    yield p
    p.close()


def test_mint_and_resolve_paid(provider):
    admin = AdminService(provider.users, provider.api_keys)
    key, prefix = admin.mint_key("owner@example.com", "paid")
    assert key.startswith("ti_")

    ent = EntitlementService(provider.api_keys, provider.devices)
    assert ent.resolve(security.hash_key(key), "dev-1") == "paid"


def test_unknown_key_is_free(provider):
    ent = EntitlementService(provider.api_keys, provider.devices)
    assert ent.resolve(security.hash_key("ti_bogus"), "dev-1") == "free"


def test_device_cap_enforced(provider):
    admin = AdminService(provider.users, provider.api_keys)
    key, _ = admin.mint_key("owner@example.com", "paid")
    ent = EntitlementService(provider.api_keys, provider.devices)
    h = security.hash_key(key)

    assert ent.resolve(h, "dev-1") == "paid"          # device 1
    assert ent.resolve(h, "dev-2") == "paid"          # device 2
    assert ent.resolve(h, "dev-3") == "device_limit"  # 3rd blocked
    assert ent.resolve(h, "dev-1") == "paid"          # known device still fine


def test_set_tier_changes_resolution(provider):
    admin = AdminService(provider.users, provider.api_keys)
    key, prefix = admin.mint_key("owner@example.com", "trial")
    ent = EntitlementService(provider.api_keys, provider.devices)
    h = security.hash_key(key)
    assert ent.resolve(h, "dev-1") == "trial"

    admin.set_tier(prefix, "expired")
    # new device to avoid the touch path; tier now reflects the change
    assert ent.resolve(h, "dev-9") == "expired"


def test_list_keys_composes_email(provider):
    admin = AdminService(provider.users, provider.api_keys)
    admin.mint_key("a@example.com", "paid")
    rows = admin.list_keys()
    assert rows[0]["email"] == "a@example.com"
    assert rows[0]["tier"] == "paid"


def test_factory_selects_duckdb(tmp_path):
    from tabint_control.db import create_database, DuckDBDatabase

    db = create_database(str(tmp_path / "x.duckdb"))
    assert isinstance(db, DuckDBDatabase)
    db.close()
