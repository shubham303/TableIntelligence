"""Outreach MCP tools — templates, campaigns, prospect emails, received email,
plus the reports tools (save/list/get reports & folders). All are a thin data/CRUD
surface over the user's Table Intelligence account via the integration control-plane
client; they do NOT send email (sending is the user's own email tool/MCP).

Extracted verbatim from the legacy god-module so the tool signatures and docstrings
are unchanged. No client-side gating: the API enforces entitlement server-side.
"""
from tabint.integration.service import platform as _platform
from tabint.shared.server import mcp

_NEED_KEY = {
    "ok": False,
    "error": "not_configured",
    "message": "Set TABINT_API_KEY (from your account at shubhamrandive.com) to use reports.",
}


_NEED_KEY_OUTREACH = {
    "ok": False,
    "error": "not_configured",
    "message": "Set TABINT_API_KEY (from your account at shubhamrandive.com) to use outreach.",
}


def _cfg(fn, *a, **k):
    return fn(*a, **k) if _platform.configured() else _NEED_KEY_OUTREACH


# --------------------------------------------------------------------------- #
# reports — save/organize analysis on the Table Intelligence platform
# (the MCP holds no user data; these call the website APIs with the user's key)
# --------------------------------------------------------------------------- #

_NEED_KEY = {
    "ok": False,
    "error": "not_configured",
    "message": "Set TABINT_API_KEY (from your account at shubhamrandive.com) to use reports.",
}


@mcp.tool()
def save_report(title: str, content: str, folder_id: str | None = None) -> dict:
    """Save a report to your Table Intelligence account to view later on the website
    dashboard. Needs an active trial or premium. `content` is the markdown report you
    compose from the analysis — ALWAYS include the findings together with their trust
    level and caveats (and note anything the tools declined to answer)."""
    return _platform.save_report(title, content, folder_id) if _platform.configured() else _NEED_KEY


@mcp.tool()
def list_reports(folder_id: str | None = None) -> dict:
    """List reports saved to your account (optionally within a folder)."""
    return _platform.list_reports(folder_id) if _platform.configured() else _NEED_KEY


@mcp.tool()
def get_report(report_id: str) -> dict:
    """Fetch a saved report's full content by id."""
    return _platform.get_report(report_id) if _platform.configured() else _NEED_KEY


@mcp.tool()
def create_folder(name: str) -> dict:
    """Create a folder in your account to organize reports."""
    return _platform.create_folder(name) if _platform.configured() else _NEED_KEY


@mcp.tool()
def list_folders() -> dict:
    """List your report folders."""
    return _platform.list_folders() if _platform.configured() else _NEED_KEY


# --------------------------------------------------------------------------- #
# outreach connector — templates → campaigns → prospect emails, plus received
# email. A data/CRUD surface on the user's Table Intelligence account; it does
# NOT send email. Typical flow:
#   1. outreach_create_template(title, prompt)      — the reusable playbook
#   2. outreach_setup_campaign(template_id)         — freezes the prompt, empty
#   3. research prospects on the web, then for each:
#      outreach_add_email(campaign_id, recipients, subject, body, details, email_ids)
#   4. user reviews/edits in the dashboard (or via outreach_update_email)
#   5. send each with your OWN email tool (Gmail/SMTP MCP), then
#      outreach_update_email(email_id, {"status": "sent"})   — record the result
#   Skip any email the user deleted/disapproved (it won't be in the list).
# No client-side gating: the API enforces entitlement server-side.
# --------------------------------------------------------------------------- #

_NEED_KEY_OUTREACH = {
    "ok": False,
    "error": "not_configured",
    "message": "Set TABINT_API_KEY (from your account at shubhamrandive.com) to use outreach.",
}


def _cfg(fn, *a, **k):
    return fn(*a, **k) if _platform.configured() else _NEED_KEY_OUTREACH


# ---- templates ----
@mcp.tool()
def outreach_create_template(title: str, prompt: str, status: str = "active") -> dict:
    """Create a reusable outreach template. `prompt` is the playbook the agent
    follows when running a campaign (who to target, how to research, tone/structure
    of the email). status: 'active' or 'inactive'."""
    return _cfg(_platform.create_template, title, prompt, status)


@mcp.tool()
def outreach_list_templates(status: str | None = None, frm: str | None = None, to: str | None = None) -> dict:
    """List outreach templates. Optional filters: status ('active'/'inactive'),
    frm/to (ISO date range on created_at)."""
    return _cfg(_platform.list_templates, status, frm, to)


@mcp.tool()
def outreach_get_template(template_id: str) -> dict:
    """Read one outreach template (title, prompt, status)."""
    return _cfg(_platform.get_template, template_id)


@mcp.tool()
def outreach_update_template(template_id: str, fields: dict) -> dict:
    """Update a template. `fields` may include title, prompt, status."""
    return _cfg(_platform.update_template, template_id, fields)


@mcp.tool()
def outreach_delete_template(template_id: str) -> dict:
    """Delete a template by id."""
    return _cfg(_platform.delete_template, template_id)


# ---- campaigns ----
@mcp.tool()
def outreach_setup_campaign(template_id: str, title: str | None = None) -> dict:
    """Start a new campaign from a template. The template's prompt is COPIED into
    the campaign (frozen — later template edits don't affect it). The campaign
    starts empty; add prospects/emails with outreach_add_email."""
    return _cfg(_platform.setup_campaign, template_id, title)


@mcp.tool()
def outreach_get_campaign(campaign_id: str) -> dict:
    """Get a campaign incl. its frozen prompt and all its drafted/sent emails."""
    return _cfg(_platform.get_campaign, campaign_id)


@mcp.tool()
def outreach_list_campaigns(status: str | None = None, template_id: str | None = None,
                            frm: str | None = None, to: str | None = None) -> dict:
    """List campaigns with optional filters (status, template_id, created_at range)."""
    return _cfg(_platform.list_campaigns, status, template_id, frm, to)


# ---- prospect emails ----
@mcp.tool()
def outreach_add_email(campaign_id: str, recipients, subject: str, body: str,
                       details: dict | None = None, email_ids: list | None = None) -> dict:
    """Add a found prospect + its drafted email to a campaign (status 'draft').
    recipients: the target email(s). details: JSON company/person metadata.
    email_ids: [{"name":..., "email":...}] contacts found. Call once per prospect
    as you research them."""
    return _cfg(_platform.add_email, campaign_id, recipients, subject, body, details, email_ids)


@mcp.tool()
def outreach_list_emails(campaign_id: str, status: str | None = None) -> dict:
    """List the emails in a campaign (with prospect details). Filter by status
    ('draft'/'sent'/'failed'). Read this before sending to get the current set."""
    return _cfg(_platform.list_emails, campaign_id, status)


@mcp.tool()
def outreach_get_email(email_id: str) -> dict:
    """Read one email entry (recipients, subject, body, status, prospect details)."""
    return _cfg(_platform.get_email, email_id)


@mcp.tool()
def outreach_update_email(email_id: str, fields: dict) -> dict:
    """Update an email. `fields` may include recipients, subject, body, status
    ('draft'/'sent'/'failed'), sent_at. After sending via your own email tool,
    set status to 'sent' to record it."""
    return _cfg(_platform.update_email, email_id, fields)


@mcp.tool()
def outreach_delete_email(email_id: str) -> dict:
    """Delete/disapprove an email (and its prospect) so it won't be sent."""
    return _cfg(_platform.delete_email, email_id)


# ---- received email (global to the user) ----
@mcp.tool()
def outreach_save_received(sender: str, subject: str, body: str, received_at: str | None = None) -> dict:
    """Save a received email to the user's account (not campaign-specific).
    received_at: ISO timestamp (defaults to now)."""
    return _cfg(_platform.save_received, sender, subject, body, received_at)


@mcp.tool()
def outreach_list_received() -> dict:
    """List received emails saved to the user's account."""
    return _cfg(_platform.list_received)


@mcp.tool()
def outreach_list_ready_to_send(campaign_id: str) -> dict:
    """Emails in a campaign that still need sending — status 'draft' or 'failed'
    (already-'sent' emails are excluded). Call this BEFORE sending so you never
    re-send. Sending itself is done by the user's OWN email tool/MCP (Resend,
    Gmail, SMTP …); this server does not send email. After each email is sent,
    record it with outreach_update_email(email_id, {"status": "sent"})."""
    return _cfg(_platform.ready_emails, campaign_id)


# ---- outreach explainer (static; no account needed) ----
@mcp.tool()
def outreach_how_it_works() -> dict:
    """Explain what the outreach agent does, step by step, and how to use it.
    Call this when the user asks what the outreach agent is, how it works, or how
    to get started. Free — no subscription required, no API key needed."""
    return {
        "name": "Outreach agent",
        "summary": (
            "Helps you run cold-outreach campaigns end to end: build a reusable "
            "template, run a campaign that researches prospects and drafts an "
            "individual cold email for each, review the drafts, then send them."
        ),
        "does_not_send_email": True,
        "sending_note": (
            "This agent never sends email itself. Sending is done by a separate "
            "email tool/MCP you install (Resend, Gmail, SMTP, …). The agent "
            "surfaces ready-to-send emails and records the result after each send."
        ),
        "steps": [
            {
                "n": 1,
                "name": "Create a template",
                "how": (
                    "The agent interviews you about your offer, audience, regions, "
                    "target roles, tone, email structure, and personalization — "
                    "iterating until you're happy — then saves a reusable template "
                    "(the playbook every campaign follows)."
                ),
                "tool": "outreach_create_template",
            },
            {
                "n": 2,
                "name": "Run a campaign",
                "how": (
                    "You pick a template and say 'run a campaign'. The agent "
                    "freezes the template into a campaign, researches prospects "
                    "(default 50), finds decision-makers and their emails, and "
                    "drafts one cold email per prospect — autonomously. Optional "
                    "extra instructions for that run are layered on top."
                ),
                "tools": ["outreach_setup_campaign", "outreach_add_email"],
            },
            {
                "n": 3,
                "name": "Stop & report",
                "how": (
                    "Once every email is drafted, the agent stops and tells you "
                    "to review. It does NOT send at this stage."
                ),
            },
            {
                "n": 4,
                "name": "Review & edit",
                "how": (
                    "Review drafts in the web dashboard, or ask the agent to show "
                    "or edit specific emails. Delete an email to drop it from the "
                    "send set."
                ),
                "tools": ["outreach_list_emails", "outreach_update_email",
                          "outreach_delete_email"],
            },
            {
                "n": 5,
                "name": "Send (separate step)",
                "how": (
                    "When you say 'send the emails for campaign X', the agent "
                    "lists the ready-to-send emails (skips already-sent), sends "
                    "each via YOUR email tool/MCP, then marks each 'sent'. Running "
                    "a campaign and sending are always separate — never combined."
                ),
                "tools": ["outreach_list_ready_to_send", "outreach_update_email"],
            },
        ],
        "get_started": (
            "To begin, ask the agent to create a new outreach template (it will "
            "interview you), or ask 'what can the outreach agent do?' for a tour."
        ),
        "default_prospects_per_campaign": 50,
        "load_playbook_prompt": "outreach_agent",
    }
