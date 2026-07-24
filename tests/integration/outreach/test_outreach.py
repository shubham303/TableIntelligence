"""Integration tests for the outreach CRUD surface + the explainer tool.

The MCP server imposes no role gating; it only checks that an API key is
configured (the ``_cfg`` helper) before calling the platform — a missing key
surfaces a ``not_configured`` hint rather than hitting the network and 401-ing.
The platform functions themselves are monkeypatched here (they are the one
external dependency); everything else runs unmodified.

The pure prompt tests live in ``unit/outreach/test_prompts.py``.

Mirrors: src/tabint/outreach/tools.py
"""
import pytest

from tabint.outreach import tools as M
from tabint.integration.service import platform as _platform
from tabint.integration.service import entitlement


# --- the explainer tool (static; no account/key needed) --------------------- #

def test_how_it_works_is_static_dict_with_five_steps():
    r = M.outreach_how_it_works()
    assert isinstance(r, dict)
    assert r["name"] == "Outreach agent"
    assert r["does_not_send_email"] is True
    assert r["default_prospects_per_campaign"] == 50
    steps = r["steps"]
    assert [s["n"] for s in steps] == [1, 2, 3, 4, 5]
    assert r["load_playbook_prompt"] == "outreach_agent"


def test_how_it_works_needs_no_key():
    # The unit conftest clears the env; the tool is static and must return its
    # payload (not a not_configured / error hint).
    r = M.outreach_how_it_works()
    assert r.get("error") is None
    assert r.get("name") == "Outreach agent"


# --- ready-to-send filter --------------------------------------------------- #

def _platform_configured(monkeypatch):
    """Tell _cfg an API key is set so the tool body runs (CI has no key). The
    MCP no longer role-gates, so this is the only stub the tests need."""
    monkeypatch.setattr(_platform, "configured", lambda: True)


def test_ready_emails_filters_out_sent(monkeypatch):
    _platform_configured(monkeypatch)
    payload = {"emails": [
        {"id": "e1", "status": "draft"},
        {"id": "e2", "status": "sent"},
        {"id": "e3", "status": "failed"},
        {"id": "e4", "status": "sent"},
        {"id": "e5", "status": "draft"},
    ]}
    monkeypatch.setattr(_platform, "list_emails", lambda cid, status=None: payload)
    r = M.outreach_list_ready_to_send("c1")
    ids = sorted(e["id"] for e in r["emails"])
    assert ids == ["e1", "e3", "e5"]        # 'sent' dropped; draft+failed kept


def test_ready_emails_handles_missing_envelope(monkeypatch):
    _platform_configured(monkeypatch)
    # Defensive: API unexpectedly returns an error dict instead of {emails: [...]}
    monkeypatch.setattr(_platform, "list_emails", lambda cid, status=None: {"error": "oops"})
    r = M.outreach_list_ready_to_send("c1")
    assert r == {"error": "oops"}           # pass-through, no crash


def test_platform_ready_emails_does_not_mutate_input(monkeypatch):
    src = {"emails": [{"status": "sent"}, {"status": "draft"}]}
    monkeypatch.setattr(_platform, "list_emails", lambda cid, status=None: src)
    out = _platform.ready_emails("c1")
    assert out is not src and src["emails"] == [
        {"status": "sent"}, {"status": "draft"},
    ]                                       # original list untouched
    assert [e["status"] for e in out["emails"]] == ["draft"]


# --- no client-side gating on the CRUD surface ------------------------------ #

# Valid positional args for each tool so the body actually runs (now that the
# tools aren't short-circuited by a decorator before the signature is consumed).
_TOOL_ARGS = {
    "outreach_create_template": ("t", "p"),
    "outreach_setup_campaign": ("t",),
    "outreach_add_email": ("c", ["r"], "s", "b"),
    "outreach_list_emails": ("c",),
    "outreach_update_email": ("e", {"status": "sent"}),
    "outreach_delete_email": ("e",),
    "outreach_list_ready_to_send": ("c",),
    "outreach_list_received": (),
}


@pytest.mark.parametrize("tool", list(_TOOL_ARGS))
def test_outreach_crud_tools_not_role_gated(monkeypatch, tool):
    # Even with a FREE role and a configured key, the tool must reach the
    # platform layer (not short-circuit to a pro_feature upgrade dict). We stub
    # the platform call to assert the body ran.
    monkeypatch.setattr(entitlement, "is_pro", lambda: False)
    monkeypatch.setattr(entitlement, "role", lambda: "free")
    monkeypatch.setattr(_platform, "configured", lambda: True)
    monkeypatch.setattr(_platform, "list_emails", lambda *a, **k: {"emails": []})
    monkeypatch.setattr(_platform, "list_received", lambda *a, **k: {"emails": []})
    monkeypatch.setattr(_platform, "create_template", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(_platform, "setup_campaign", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(_platform, "add_email", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(_platform, "update_email", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(_platform, "delete_email", lambda *a, **k: {"ok": True})
    fn = getattr(M, tool)
    r = fn(*_TOOL_ARGS[tool])
    assert r.get("error") != "pro_feature"   # not role-gated


def test_outreach_crud_tools_hint_when_no_key(monkeypatch):
    # With no API key configured, tools surface a not_configured hint rather
    # than making a doomed HTTP call. (Key-presence check, not role gating.)
    monkeypatch.setattr(_platform, "configured", lambda: False)
    r = M.outreach_list_received()
    assert r.get("error") == "not_configured"
