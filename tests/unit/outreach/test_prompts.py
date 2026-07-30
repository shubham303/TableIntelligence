"""Tests for the outreach agent prompt (pure — no platform calls).

The CRUD/platform outreach tests live in
``integration/outreach/test_outreach.py``.

Mirrors: src/tabint/outreach/prompts.py
"""
from tabint.outreach import prompts


# --- the agent prompt ------------------------------------------------------- #

def test_outreach_agent_prompt_is_non_empty_string():
    p = prompts.outreach_agent()
    assert isinstance(p, str) and len(p) > 500


def test_outreach_agent_prompt_covers_five_stages():
    p = prompts.outreach_agent()
    for marker in (
        "STAGE 1", "STAGE 2", "STAGE 3", "STAGE 4", "STAGE 5",
        "CREATE A TEMPLATE", "RUN A CAMPAIGN", "STOP & REPORT",
        "REVIEW & EDIT", "SEND",
    ):
        assert marker in p, f"prompt missing stage marker: {marker!r}"


def test_outreach_agent_prompt_states_it_does_not_send_email():
    p = prompts.outreach_agent()
    assert "DOES NOT SEND EMAIL" in p or "do not send email" in p.lower()
    # and the send stage must defer to the user's own email tool
    assert "email tool" in p.lower() or "email mcp" in p.lower()


def test_outreach_agent_prompt_carries_default_prospect_count_and_disambiguation():
    p = prompts.outreach_agent()
    assert "50" in p                      # default prospects per campaign
    assert "Disambiguation".lower() in p.lower() or "DISAMBIGUATION" in p


def test_outreach_agent_prompt_lists_the_tools():
    p = prompts.outreach_agent()
    for tool in (
        "outreach_create_template", "outreach_setup_campaign", "outreach_add_email",
        "outreach_list_ready_to_send", "outreach_update_email",
    ):
        assert tool in p, f"prompt missing tool reference: {tool!r}"
