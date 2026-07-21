"""Tests for the outreach agent surface: the agent prompt, the free explainer
tool, the ready-to-send filter, and paid-tier gating on the CRUD tools.

Tools are called directly (same pattern as test_mcp_server.py). `requires_paid`
wraps the CRUD tools; with no TABINT_API_KEY in CI, `tier()` resolves to "free"
and they short-circuit to an upgrade dict. We force "paid" via monkeypatch where
we need the tool body to actually run.
"""
import pytest

from tabint import mcp_server as M
from tabint import platform as _platform


# --- the agent prompt ------------------------------------------------------- #

def test_outreach_agent_prompt_is_non_empty_string():
    p = M.outreach_agent()
    assert isinstance(p, str) and len(p) > 500


def test_outreach_agent_prompt_covers_five_stages():
    p = M.outreach_agent()
    for marker in (
        "STAGE 1", "STAGE 2", "STAGE 3", "STAGE 4", "STAGE 5",
        "CREATE A TEMPLATE", "RUN A CAMPAIGN", "STOP & REPORT",
        "REVIEW & EDIT", "SEND",
    ):
        assert marker in p, f"prompt missing stage marker: {marker!r}"


def test_outreach_agent_prompt_states_it_does_not_send_email():
    p = M.outreach_agent()
    assert "DOES NOT SEND EMAIL" in p or "do not send email" in p.lower()
    # and the send stage must defer to the user's own email tool
    assert "email tool" in p.lower() or "email mcp" in p.lower()


def test_outreach_agent_prompt_carries_default_prospect_count_and_disambiguation():
    p = M.outreach_agent()
    assert "50" in p                      # default prospects per campaign
    assert "Disambiguation".lower() in p.lower() or "DISAMBIGUATION" in p


def test_outreach_agent_prompt_lists_the_tools():
    p = M.outreach_agent()
    for tool in (
        "outreach_create_template", "outreach_setup_campaign", "outreach_add_email",
        "outreach_list_ready_to_send", "outreach_update_email",
    ):
        assert tool in p, f"prompt missing tool reference: {tool!r}"


# --- the free explainer tool (no paid gating, no API key needed) ------------- #

def test_how_it_works_is_static_dict_with_five_steps():
    r = M.outreach_how_it_works()
    assert isinstance(r, dict)
    assert r["name"] == "Outreach agent"
    assert r["does_not_send_email"] is True
    assert r["default_prospects_per_campaign"] == 50
    steps = r["steps"]
    assert [s["n"] for s in steps] == [1, 2, 3, 4, 5]
    assert r["load_playbook_prompt"] == "outreach_agent"


def test_how_it_works_callable_without_paid_tier():
    # No TABINT_API_KEY in CI → tier is "free". If the tool were accidentally
    # wrapped by requires_paid, it would return {"error": "paid_feature"}.
    r = M.outreach_how_it_works()
    assert r.get("error") != "paid_feature"


# --- ready-to-send filter --------------------------------------------------- #

def _force_paid(monkeypatch):
    """Bypass entitlement AND the API-key-configured check so the wrapped tool
    body actually runs (CI has no TABINT_API_KEY)."""
    monkeypatch.setattr(M.entitlement, "is_paid", lambda: True)
    monkeypatch.setattr(M.entitlement, "tier", lambda: "paid")
    monkeypatch.setattr(_platform, "configured", lambda: True)


def test_ready_emails_filters_out_sent(monkeypatch):
    _force_paid(monkeypatch)
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
    _force_paid(monkeypatch)
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


# --- paid gating regression on the CRUD surface ----------------------------- #

@pytest.mark.parametrize("tool", [
    "outreach_create_template", "outreach_setup_campaign", "outreach_add_email",
    "outreach_list_emails", "outreach_update_email", "outreach_delete_email",
    "outreach_list_ready_to_send", "outreach_list_received",
])
def test_outreach_crud_tools_are_paid_gated(monkeypatch, tool):
    # Force FREE explicitly and stub the platform so the test is robust to a real
    # API key in the env. requires_paid runs first → returns paid_feature before
    # any HTTP call, so the platform stub never runs.
    monkeypatch.setattr(M.entitlement, "is_paid", lambda: False)
    monkeypatch.setattr(M.entitlement, "tier", lambda: "free")
    monkeypatch.setattr(_platform, "configured", lambda: True)
    fn = getattr(M, tool)
    r = fn("x")
    assert r.get("error") == "paid_feature"
