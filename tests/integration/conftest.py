"""Integration-test conftest — autouse isolation for shared module state.

Integration tests keep the real DuckDB / filesystem in the loop (only the
network is mocked). These autouse fixtures ensure the global state those layers
hang off — the live session registry, the session base directory, and the
scratchpad directory — is redirected into each test's ``tmp_path`` so no run
ever pollutes the developer's home directory or leaks state to a neighbour.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_sessions(tmp_path, monkeypatch):
    """Redirect the MCP server's session root into tmp_path and clear the registry.

    Promoted from test_mcp_server.py's ``isolate`` autouse fixture; now applies
    to every integration test so none accidentally writes under the real CWD.
    """
    from tabint.shared import server
    monkeypatch.setattr(server, "_BASE", str(tmp_path))
    server._SESSIONS.clear()
    yield
    server._SESSIONS.clear()


@pytest.fixture(autouse=True)
def _isolate_scratchpad(tmp_path, monkeypatch):
    """Redirect the scratchpad directory into tmp_path (never ~/.tableintelligence).

    Promoted from test_scratchpad.py's ``isolate_dir`` autouse fixture.
    """
    from tabint.shared import scratchpad
    monkeypatch.setattr(scratchpad, "_DIR", tmp_path / ".tableintelligence")
