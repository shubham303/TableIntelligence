"""Root conftest — shared fixtures for both unit and integration tests.

This consolidates the helpers that were copy-pasted across the flat test files
(``_session``, ``_csv``, ``_run``, ``_fixtures``, ``linked``). Test files should
reach for these instead of redefining their own.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

# Resolved once at import time. Using __file__ (not the pytest rootdir) keeps
# fixture resolution stable regardless of which subdirectory a test lives in.
FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ── fixture data location ──────────────────────────────────────────────────

@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Absolute path to ``tests/fixtures/`` (the bundled *.csv datasets)."""
    return FIXTURES_DIR


# ── CSV / Session helpers (the old _session / _csv / _fixtures / linked) ─────

def copy_fixture(name: str, tmp_path: Path) -> Path:
    """Copy a bundled ``tests/fixtures/<name>`` file into tmp_path; return dst.

    Replaces the per-file ``_session``/``_fixtures``/``_csv`` copy blocks.
    """
    dst = tmp_path / name
    shutil.copy(FIXTURES_DIR / name, dst)
    return dst


def copy_fixtures(tmp_path: Path, *names: str) -> list[str]:
    """Copy several bundled fixtures; return their destination paths as strings."""
    return [str(copy_fixture(n, tmp_path)) for n in names]


def write_csv(df, tmp_path: Path, name: str) -> str:
    """Write a DataFrame to ``tmp_path/<name>``; return the path string.

    Replaces the four duplicated ``_csv(tmp_path, name, df)`` helpers.
    """
    p = tmp_path / name
    df.to_csv(p, index=False)
    return str(p)


@pytest.fixture
def csv_writer(tmp_path):
    """Factory fixture: ``csv_writer(df, "x.csv")`` -> path string."""
    def _write(df, name):
        return write_csv(df, tmp_path, name)
    return _write


def load_session(name: str, tmp_path: Path):
    """Load a single bundled CSV into an in-memory ``Session`` (no persistence).

    Replaces ``_session("employees.csv", tmp_path)`` in test_analytics /
    test_feature_computation.
    """
    from tabint import Session
    return Session.load(str(copy_fixture(name, tmp_path)))


@pytest.fixture
def session_loader(tmp_path):
    """Factory fixture: ``session_loader("customers.csv")`` -> a fresh Session."""
    def _load(name):
        return load_session(name, tmp_path)
    return _load


@pytest.fixture
def linked_session(tmp_path):
    """A multi-table Session: orders → customers + orders → products.

    Promoted from test_workspace.py's ``linked`` fixture.
    """
    from tabint import Session
    paths = copy_fixtures(tmp_path, "orders.csv", "customers.csv", "products.csv")
    return Session.load(paths)


# ── CLI runner (the old _run) ──────────────────────────────────────────────

def run_cli(capsys, argv) -> tuple[int, dict]:
    """Invoke the tabint CLI in-process, returning ``(exit_code, parsed_json)``.

    Replaces the ``_run`` helpers in test_cli.py / test_v1_fixes.py.
    """
    from tabint.app.cli import main
    code = main(argv)
    out = capsys.readouterr().out
    return code, json.loads(out)


@pytest.fixture
def cli_runner(capsys):
    """Factory fixture: ``cli_runner(["--base", str(tmp_path), "load", ...])``."""
    def _run(argv):
        return run_cli(capsys, argv)
    return _run


# ── database / deps fixture ────────────────────────────────────────────────

@pytest.fixture
def db(tmp_path, monkeypatch):
    """Point the MCP server at a temp session root and clear the live registry.

    The canonical "deps" fixture for any test that touches session state.
    Promoted from test_mcp_server.py's ``isolate`` autouse fixture; made
    explicit (not autouse) so individual tests opt in.
    """
    from tabint.shared import server
    monkeypatch.setattr(server, "_BASE", str(tmp_path))
    server._SESSIONS.clear()
    yield tmp_path
    server._SESSIONS.clear()
