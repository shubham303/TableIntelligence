"""MCP server exposing the deterministic core to agent tools (e.g. Claude Cowork).

The model is session-key centric, exactly as an agent expects: call
``create_session`` once to get a ``session_key``, then pass that key to every
later tool to identify the session and its data. Sessions are held live in an
in-memory registry for speed and backed by the on-disk persistence layer, so a
key keeps working across server restarts (a cache miss reopens it from disk).

Run with:  ``python -m tabint.mcp_server``  (stdio transport).
Set ``TABULAR_BASE`` to control where sessions are stored (default: cwd).
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import connectors, entitlement, persistence, scratchpad
from . import platform as _platform
from ._serialize import jsonable as _jsonable, result_dict as _result
from .results import Result
from .session import Session

_INSTRUCTIONS = """Deterministic single-table data analysis. Workflow:
1. create_session(paths) -> returns a session_key plus the tables and detected
   foreign-key relationships. Pass the session_key to every subsequent tool.
2. Every analytic runs on ONE table (an uploaded table or one produced by join).
   For multiple related tables, call join(session_key, tables) to materialize a
   combined table, then run analytics on it.
3. Each tool returns a structured result: the chosen method, a one-line summary,
   the values (statistics/scores), and metadata (assumptions, params). Trust the
   method it picked — test/algorithm selection is made deterministically.
4. Every result also carries a `trust` block (a confidence level —
   high/moderate/low/none/unassessed — plus caveats) and a `declined` flag. When
   `declined` is true the data cannot support the question: report the refusal and
   its reason and do NOT substitute a number. Always convey the trust level and
   caveats to the user; never present a low-trust or declined result as a
   confident fact."""

mcp = FastMCP("tabint", instructions=_INSTRUCTIONS)

_BASE = os.environ.get("TABULAR_BASE") or "."
_SESSIONS: dict[str, Session] = {}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _get(session_key: str) -> Session:
    """Resolve a session by key, reopening from disk on a cache miss."""
    session = _SESSIONS.get(session_key)
    if session is None:
        session = persistence.open_session(session_key, base=_BASE)  # raises if unknown
        _SESSIONS[session_key] = session
    return session


def _summary(session: Session) -> dict:
    return {
        "session_key": session.id,
        "tables": session.tables,
        "relationships": _jsonable(session.relationships().model_dump()),
    }


# --------------------------------------------------------------------------- #
# session lifecycle
# --------------------------------------------------------------------------- #

@mcp.tool()
def create_session(paths: list[str]) -> dict:
    """Create a session from one or more CSV paths. Returns the session_key,
    the loaded table names, and the auto-detected foreign-key relationships."""
    session = persistence.create_session(paths, base=_BASE)
    _SESSIONS[session.id] = session
    return _summary(session)


@mcp.tool()
def list_sessions() -> list[str]:
    """List the keys of all persisted sessions."""
    return persistence.list_sessions(base=_BASE)


@mcp.tool()
def account_status() -> dict:
    """Show this install's subscription tier and whether paid features
    (connectors, cloud artifact storage) are unlocked. All analytics tools are
    free; this only reports entitlement for the paid surface."""
    return entitlement.status()


# --------------------------------------------------------------------------- #
# connectors (paid) — pull a source into a session, normalized to the contract
# --------------------------------------------------------------------------- #

@mcp.tool()
def list_connectors() -> dict:
    """List available data-source connectors (e.g. 'stripe'). Connectors are a
    paid feature; analysis of local files is always free."""
    return {"connectors": connectors.list_connectors(), "paid_feature": True}


@mcp.tool()
@entitlement.requires_paid
def connect_stripe(limit: int = 1000, stripe_key: str | None = None) -> dict:
    """Pull your Stripe data (charges, customers, subscriptions, invoices) into a
    new analysis session, normalized to canonical tables. PAID feature.

    The key is read from STRIPE_API_KEY or TABINT_STRIPE_KEY if `stripe_key` is not
    passed (a test-mode `sk_test_...` key is fine to start). Your data is fetched
    directly from Stripe to this machine and never sent anywhere else. Then run the
    standard analytics tools on the returned session_key (see the 'stripe' prompt)."""
    import tempfile

    key = stripe_key or os.environ.get("TABINT_STRIPE_KEY") or os.environ.get("STRIPE_API_KEY")
    if not key:
        return {
            "ok": False,
            "error": "no_credentials",
            "message": "Set STRIPE_API_KEY (or TABINT_STRIPE_KEY) to a Stripe secret key "
                       "like sk_test_..., or pass stripe_key.",
        }
    conn = connectors.get_connector("stripe")
    tables = conn.fetch(key, limit=limit)
    dest = tempfile.mkdtemp(prefix="tabint_stripe_")
    paths = conn.materialize(tables, dest)
    session = persistence.create_session(list(paths.values()), base=_BASE)
    _SESSIONS[session.id] = session
    out = _summary(session)
    out["row_counts"] = {k: int(len(v)) for k, v in tables.items()}
    out["playbook"] = conn.platform_prompt
    return out


@mcp.prompt()
def stripe() -> str:
    """How to analyze data connected from Stripe."""
    return connectors.get_connector("stripe").platform_prompt


# --------------------------------------------------------------------------- #
# outreach agent prompt — the behavior that makes any agent harness
# (Claude, Codex, …) act as an outreach agent. A user loads this prompt once to
# get the full step-wise playbook: build a template, run a campaign, draft
# prospect emails, review, and prepare them for sending. The MCP server only
# guides and stores data — it does NOT send email; the user's own email tool /
# MCP (Resend, Gmail, SMTP, …) does the actual sending.
# --------------------------------------------------------------------------- #

_OUTREACH_AGENT_PROMPT = """\
You are an OUTREACH AGENT. You help the user run cold-outreach campaigns end to
end: build a reusable outreach template, run prospecting campaigns that research
companies and draft individual cold emails for each prospect, and prepare those
emails for sending. You run autonomously inside the steps the user starts, and
you ask for clarification whenever intent is ambiguous.

You have a set of `outreach_*` tools that store everything in the user's web
account (the dashboard they can also open in a browser). Templates, campaigns,
prospects, drafted emails, and received replies all live there.

YOU DO NOT SEND EMAIL. Email is delivered by a SEPARATE email tool or MCP server
the user has installed (Resend, Gmail, SMTP, etc.). Your only job at the send
step is to surface the emails that are ready and, after the email tool sends
them, to record the result. Never mark an email 'sent' unless it was actually
sent by the email tool.

===============================================================================
THE WORKFLOW — five stages. Stages 1–4 are one continuous flow you drive; stage
5 (send) is a SEPARATE step the user starts explicitly. Never combine running a
campaign with sending — running a campaign only creates prospect + email DATA.
===============================================================================

STAGE 1 — CREATE A TEMPLATE (interactive; iterate until the user is satisfied).
A template is a reusable PROMPT — the playbook every later campaign follows
autonomously, without the user in the loop. Getting this prompt right is the
most important part; the whole campaign leans on it.

Interview the user. Ask the questions below (batch a few per turn, don't dump
all twelve at once). After each batch, summarize what you've captured so far,
propose defaults for anything unanswered, and keep iterating until the user is
happy. Only then assemble the answers into a single template `prompt` string and
call `outreach_create_template(title, prompt)`.

Ask:
  1. Type of outreach — what is the product/service being pitched?
  2. Who are the potential clients / audience? (industry, segment, example
     companies they admire.)
  3. Regions / countries to prospect in.
  4. Domains / industries to target, and which to avoid.
  5. What kind of companies to look for (size, stage, business model).
  6. What job titles / roles to contact inside those companies.
  7. Who within the org is the decision-maker, and the likely email format
     (e.g. first@company.com, first.last@…). How confident are we in that?
  8. Tone and voice of the email (warm/formal/casual, length, sign-off).
  9. What the email should look like — structure, the single ask, any link or
     proof (e.g. a website/portfolio) to include.
 10. Which specifics should be personalized per prospect, and which stay
     generic across the batch.
 11. How personalized should each email be — "generic with a few specifics" or
     "highly personalized per prospect"? (Trade-off: personalization raises
     reply rate but lowers volume.)
 12. What should you research about each prospect, and which of that research
     should actually appear in the email (most research informs targeting, only
     a little makes it into the body).

State your default assumptions up front (tone, length, personalization level,
default prospect count) so the user can simply confirm. The finished template
`prompt` must read as a self-contained instruction set a future campaign run
can follow with no further input — capturing audience, targeting, research plan,
email structure, tone, and personalization rules.

STAGE 2 — RUN A CAMPAIGN (autonomous, no user in the loop once started).
The user starts this in natural language, e.g. "run a campaign using the X
template" or "start outreach for Y". Steps:

  a. Pick the template. If ambiguous, list active templates via
     `outreach_list_templates` and ask which one. Accept any EXTRA PER-CAMPAGIN
     INSTRUCTIONS the user gives at run time — these layer ON TOP of the frozen
     template prompt for this run only (hold them in conversation context; you
     do not need to persist them separately).
  b. Call `outreach_setup_campaign(template_id, title)`. This FREEZES the
     template's prompt into the campaign — later template edits won't affect it.
  c. Read the frozen prompt back via `outreach_get_campaign(campaign_id)` and
     treat (frozen prompt + the user's extra instructions) as your instructions.
  d. Default to FIFTY (50) prospects unless the user asked for a different
     number. Tell the user the count as you start.
  e. Research autonomously (web search / fetch) per the template: find and
     qualify companies, then for each company find the decision-maker(s) and
     their email(s).
  f. For EACH prospect, draft one cold email following the template (tone,
     structure, personalization) and call
     `outreach_add_email(campaign_id, recipients, subject, body, details,
     email_ids)` ONCE per prospect. `details` = company/person metadata you
     found; `email_ids` = [{"name":…, "email":…}] contacts you found.

STAGE 3 — STOP & REPORT.
Once every prospect's email is drafted and saved, STOP. Do not send. Tell the
user all emails are created and they can review them — in the dashboard, or by
asking you to show/edit specific ones. This is a hard stop; sending is a
separate, explicit step the user must start.

STAGE 4 — REVIEW & EDIT.
Editing happens either in the web dashboard or via your tools:
`outreach_list_emails`, `outreach_get_email`, `outreach_update_email`,
`outreach_delete_email`. Deleting/disapproving an email removes it from the
send set automatically (it simply won't appear in the ready-to-send list).

STAGE 5 — SEND (separate step, user-initiated).
The user asks in natural language ("send the emails for campaign X"). Steps:

  a. Disambiguate the campaign if needed (see below). Never assume.
  b. Call `outreach_list_ready_to_send(campaign_id)` to get only the emails
     that still need sending (status 'draft' or 'failed'). Already-'sent'
     emails are excluded — you will never re-send.
  c. For each ready email, send it via the user's EMAIL tool/MCP (NOT a tool
     from this server — you don't have one). Only after the email tool confirms
     the send, call `outreach_update_email(email_id, {"status": "sent"})` to
     record it. If the send failed, set status to 'failed'.
  d. Report what was sent, what failed, and what was skipped (already sent).

===============================================================================
DISAMBIGUATION RULES — always ask when intent is unclear. Never guess.
===============================================================================

  • "Send emails" / "run a campaign" without naming one → list the candidates
    via `outreach_list_campaigns` and ask the user to pick.
  • Create vs. run vs. send is ambiguous → ask before acting. ("Start
    outreach" might mean create a template, run a campaign, or send — confirm.)
  • Missing required detail (template choice, prospect count, send target) →
    ask. State the sensible default alongside, so the user can just confirm.

===============================================================================
PROSPECT RESEARCH & EMAIL DISCOVERY PROTOCOL (generic; apply every campaign).
===============================================================================

For each company, qualify it before you invest in an email. A good prospect has
at least three of these five signals — if fewer than three clearly hold, SKIP:
  1. Has data / a real need for what the user offers.
  2. Can pay (budget-appropriate size/stage).
  3. A decision-maker who reads their own inbox is reachable.
  4. A recurring need (not a one-off).
  5. A researchable hook — enough public footprint to find and personalize.

Anti-targets to skip: can't/won't pay, no data relevant to the offer, no
reachable decision-maker, purely offline / no footprint.

Email discovery — in this order, per prospect:
  1. Read the company website properly: Contact, About, Team, Leadership,
     footer, privacy policy / imprint. (EU/UK sites often legally publish a
     contact email.)
  2. Targeted web search: '"<Company>" contact email',
     '"<Person>" "<company.com>" email', 'site:<company.com> email',
     '"<Person>" <company> linkedin', '"@<company.com>"'.
  3. LinkedIn and other socials.
  4. Directories — Hunter, Apollo, Clearbit, RocketReach, ZoomInfo, Crunchbase
     — treat these as HYPOTHESES, not facts.
  5. Pattern inference (first@, first.last@, …) ONLY as a last resort, ONLY if
     you've actually observed the format on a published address.

Tag every address with a confidence: `published` (live on the site / a
directory — highest), `verified` (passed a deliverability check), `inferred`
(pattern-guessed — lowest). NEVER send to an inferred address as the only
recipient. Aim for the named decision-maker; use "Hi there" only when nothing
but a generic address exists.

===============================================================================
COLD-EMAIL PRINCIPLES (generic; apply to every drafted email).
===============================================================================

  • Lead with the help, not your résumé — observation → time-framed pain → then
    credentials.
  • One clean, time-framed pain ("…takes up too much of your time"), not a
    four-verb laundry list. Frame pain as TIME, not struggle.
  • Make the capability concrete and outcome-led — name THEIR data and the
    payoff, not a generic feature list.
  • Observation, NEVER diagnosis. A light factual note about their model/
    channels is good; a presumptuous claim about what's wrong with their
    business is not.
  • Question close. No pricing in the body.
  • Vary the subject across a batch — identical subjects read as mass-mail.
  • Warm and phone-readable.
  • Include a positive where it fits; an all-criticism message reads as
    manufactured.

===============================================================================
PUBLIC-DATA GUARDRAIL — numbers from public sources are HYPOTHESES.
===============================================================================

Any figure pulled from a public source (catalog, filings, traffic estimates) is
a HYPOTHESIS. Frame it as "worth checking against your numbers," never as a
proven fact. You may note what the public data CAN'T show as a natural lead-in
to the offer.

Optional — Shopify catalog insight: if you are prospecting Shopify merchants
and it fits the template, you may fetch their public
`https://<domain>/products.json` for catalog insight to inform the email
(product count, price ladder, launch cadence). Only do this if it suits the
campaign; the user decides whether to include it. Treat every figure as a
hypothesis per the guardrail above.

===============================================================================
TOOLS YOU HAVE (all paid-gated except `outreach_how_it_works`).
===============================================================================

Templates : outreach_create_template, outreach_list_templates,
            outreach_get_template, outreach_update_template,
            outreach_delete_template
Campaigns : outreach_setup_campaign, outreach_get_campaign,
            outreach_list_campaigns
Emails    : outreach_add_email, outreach_list_emails, outreach_get_email,
            outreach_update_email, outreach_delete_email,
            outreach_list_ready_to_send   ← use this before sending
Received  : outreach_save_received, outreach_list_received
Help      : outreach_how_it_works   ← free; call when the user asks what this is

Remember: this server STORES DATA and GUIDES YOU. It does not send email. Every
send goes through the user's own email tool/MCP, and you record the result.
"""


@mcp.prompt()
def outreach_agent() -> str:
    """How to act as an outreach agent: build templates, run campaigns, draft and
    review prospect emails, and prepare them for sending via the user's own email
    MCP. Load this prompt to get the full step-wise playbook. The server stores
    data and guides you — it does NOT send email."""
    return _OUTREACH_AGENT_PROMPT


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
# A paid connector: needs trial/premium.
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
@entitlement.requires_paid
def outreach_create_template(title: str, prompt: str, status: str = "active") -> dict:
    """Create a reusable outreach template. `prompt` is the playbook the agent
    follows when running a campaign (who to target, how to research, tone/structure
    of the email). status: 'active' or 'inactive'."""
    return _cfg(_platform.create_template, title, prompt, status)


@mcp.tool()
@entitlement.requires_paid
def outreach_list_templates(status: str | None = None, frm: str | None = None, to: str | None = None) -> dict:
    """List outreach templates. Optional filters: status ('active'/'inactive'),
    frm/to (ISO date range on created_at)."""
    return _cfg(_platform.list_templates, status, frm, to)


@mcp.tool()
@entitlement.requires_paid
def outreach_get_template(template_id: str) -> dict:
    """Read one outreach template (title, prompt, status)."""
    return _cfg(_platform.get_template, template_id)


@mcp.tool()
@entitlement.requires_paid
def outreach_update_template(template_id: str, fields: dict) -> dict:
    """Update a template. `fields` may include title, prompt, status."""
    return _cfg(_platform.update_template, template_id, fields)


@mcp.tool()
@entitlement.requires_paid
def outreach_delete_template(template_id: str) -> dict:
    """Delete a template by id."""
    return _cfg(_platform.delete_template, template_id)


# ---- campaigns ----
@mcp.tool()
@entitlement.requires_paid
def outreach_setup_campaign(template_id: str, title: str | None = None) -> dict:
    """Start a new campaign from a template. The template's prompt is COPIED into
    the campaign (frozen — later template edits don't affect it). The campaign
    starts empty; add prospects/emails with outreach_add_email."""
    return _cfg(_platform.setup_campaign, template_id, title)


@mcp.tool()
@entitlement.requires_paid
def outreach_get_campaign(campaign_id: str) -> dict:
    """Get a campaign incl. its frozen prompt and all its drafted/sent emails."""
    return _cfg(_platform.get_campaign, campaign_id)


@mcp.tool()
@entitlement.requires_paid
def outreach_list_campaigns(status: str | None = None, template_id: str | None = None,
                            frm: str | None = None, to: str | None = None) -> dict:
    """List campaigns with optional filters (status, template_id, created_at range)."""
    return _cfg(_platform.list_campaigns, status, template_id, frm, to)


# ---- prospect emails ----
@mcp.tool()
@entitlement.requires_paid
def outreach_add_email(campaign_id: str, recipients, subject: str, body: str,
                       details: dict | None = None, email_ids: list | None = None) -> dict:
    """Add a found prospect + its drafted email to a campaign (status 'draft').
    recipients: the target email(s). details: JSON company/person metadata.
    email_ids: [{"name":..., "email":...}] contacts found. Call once per prospect
    as you research them."""
    return _cfg(_platform.add_email, campaign_id, recipients, subject, body, details, email_ids)


@mcp.tool()
@entitlement.requires_paid
def outreach_list_emails(campaign_id: str, status: str | None = None) -> dict:
    """List the emails in a campaign (with prospect details). Filter by status
    ('draft'/'sent'/'failed'). Read this before sending to get the current set."""
    return _cfg(_platform.list_emails, campaign_id, status)


@mcp.tool()
@entitlement.requires_paid
def outreach_get_email(email_id: str) -> dict:
    """Read one email entry (recipients, subject, body, status, prospect details)."""
    return _cfg(_platform.get_email, email_id)


@mcp.tool()
@entitlement.requires_paid
def outreach_update_email(email_id: str, fields: dict) -> dict:
    """Update an email. `fields` may include recipients, subject, body, status
    ('draft'/'sent'/'failed'), sent_at. After sending via your own email tool,
    set status to 'sent' to record it."""
    return _cfg(_platform.update_email, email_id, fields)


@mcp.tool()
@entitlement.requires_paid
def outreach_delete_email(email_id: str) -> dict:
    """Delete/disapprove an email (and its prospect) so it won't be sent."""
    return _cfg(_platform.delete_email, email_id)


# ---- received email (global to the user) ----
@mcp.tool()
@entitlement.requires_paid
def outreach_save_received(sender: str, subject: str, body: str, received_at: str | None = None) -> dict:
    """Save a received email to the user's account (not campaign-specific).
    received_at: ISO timestamp (defaults to now)."""
    return _cfg(_platform.save_received, sender, subject, body, received_at)


@mcp.tool()
@entitlement.requires_paid
def outreach_list_received() -> dict:
    """List received emails saved to the user's account."""
    return _cfg(_platform.list_received)


@mcp.tool()
@entitlement.requires_paid
def outreach_list_ready_to_send(campaign_id: str) -> dict:
    """Emails in a campaign that still need sending — status 'draft' or 'failed'
    (already-'sent' emails are excluded). Call this BEFORE sending so you never
    re-send. Sending itself is done by the user's OWN email tool/MCP (Resend,
    Gmail, SMTP …); this server does not send email. After each email is sent,
    record it with outreach_update_email(email_id, {"status": "sent"})."""
    return _cfg(_platform.ready_emails, campaign_id)


# ---- outreach explainer (free; not paid-gated) ----
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





@mcp.tool()
def session_info(session_key: str) -> dict:
    """Return a session's tables and detected relationships."""
    return _summary(_get(session_key))


@mcp.tool()
def add_table(session_key: str, path: str) -> dict:
    """Load another CSV into an existing session as a new table."""
    session = _get(session_key)
    table = session.add_table(path)
    return {"session_key": session_key, "added_table": table.name, "tables": session.tables}


# --------------------------------------------------------------------------- #
# scratchpad: your own plain-text notebook for this session
# --------------------------------------------------------------------------- #

@mcp.tool()
def scratchpad_add(session_key: str, text: str) -> dict:
    """Append a note to this session's scratchpad — your own working memory.

    Write free-form English whenever you want to remember something across steps:
    a finding, a thing you tried and its outcome, a hypothesis, a reminder. Each
    note is stamped with the current date-time automatically. This is separate from
    the data — use it so you can pick up where you left off without recomputing.
    """
    _get(session_key)  # require a live session; raises if the key is unknown
    stamp = scratchpad.add(session_key, text)
    return {"session_key": session_key, "written_at": stamp}


@mcp.tool()
def scratchpad_read(session_key: str) -> dict:
    """Read back everything you've written to this session's scratchpad, in order."""
    _get(session_key)  # require a live session; raises if the key is unknown
    return {"session_key": session_key, "text": scratchpad.read(session_key)}


@mcp.tool()
def scratchpad_search(session_key: str, query: str) -> dict:
    """Search your scratchpad notes for `query` (simple case-insensitive text match).

    Returns the timestamped notes that mention the query — e.g. search "salary" to
    recall everything you noted about salary.
    """
    _get(session_key)  # require a live session; raises if the key is unknown
    return {"session_key": session_key, "matches": scratchpad.search(session_key, query)}


# --------------------------------------------------------------------------- #
# structure: relationships, join, sql
# --------------------------------------------------------------------------- #

@mcp.tool()
def relationships(session_key: str) -> dict:
    """Detect and return the foreign-key graph across the session's tables."""
    return _jsonable(_get(session_key).relationships().model_dump())


@mcp.tool()
def join(session_key: str, tables: list[str], name: str | None = None, how: str = "left") -> dict:
    """Join tables along detected foreign keys into a new table; returns its name and columns."""
    joined = _get(session_key).join(tables, name=name, how=how)
    frame = joined.get_frame()
    return {"table": joined.name, "columns": list(frame.columns), "n_rows": int(len(frame))}


@mcp.tool()
def run_sql(session_key: str, query: str, limit: int = 1000) -> dict:
    """Run a read-only SQL SELECT across the session's tables (each visible by name).
    Rows are capped at `limit`. To build or fill tables, use create_table / insert_into."""
    frame = _get(session_key).run_sql(query)
    total = int(len(frame))
    records = _jsonable(frame.head(limit).to_dict(orient="records"))
    return {"n_rows": total, "truncated": total > limit, "rows": records}


@mcp.tool()
def create_table(
    session_key: str,
    name: str,
    columns: list[dict] | None = None,
    select_sql: str | None = None,
) -> dict:
    """Create a new clean, structured table in the session.

    Use this when the source data is messy or badly shaped: define the correct
    schema here, then copy the data across with insert_into (one query at a time
    or in bulk). run_sql cannot create tables — this is the tool that does.

    Two mutually exclusive modes (pass exactly one):
    - columns: an empty typed table. Each entry is {"name": "...", "type": "..."},
      e.g. [{"name": "order_id", "type": "BIGINT"}, {"name": "amount", "type": "DECIMAL(10,2)"}].
      Allowed types are the standard SQL/DuckDB types (INTEGER, BIGINT, DOUBLE,
      DECIMAL(p,s), VARCHAR, DATE, TIMESTAMP, BOOLEAN, ...).
    - select_sql: materialize a query over the existing tables as a new table in
      one shot (e.g. "SELECT trim(name) AS name, CAST(qty AS INTEGER) AS qty FROM raw").

    Returns the created table's name and columns.
    """
    cols = None
    if columns is not None:
        cols = [(c["name"], c["type"]) for c in columns]
    table = _get(session_key).create_table(name, columns=cols, select_sql=select_sql)
    frame = table.get_frame()
    return {"table": table.name, "columns": list(frame.columns), "n_rows": int(len(frame))}


@mcp.tool()
def insert_into(session_key: str, name: str, source_sql: str) -> dict:
    """Copy rows into an existing table (partner of create_table's `columns` mode).

    `source_sql` is a SELECT or VALUES query whose columns map positionally to the
    target table's columns, e.g.
      "SELECT trim(customer) AS name, CAST(spend AS DECIMAL(10,2)) FROM raw WHERE spend IS NOT NULL"
    or "VALUES ('Acme', 12.50), ('Globex', 9.99)".
    Call repeatedly to build a table up from many messy sources. Returns the
    number of rows inserted and the table's new total row count.
    """
    session = _get(session_key)
    inserted = session.insert_into(name, source_sql)
    total = int(len(session.table(name).get_frame()))
    return {"table": name, "inserted": inserted, "n_rows": total}


# --------------------------------------------------------------------------- #
# descriptive
# --------------------------------------------------------------------------- #

@mcp.tool()
def count_rows(session_key: str, table: str) -> dict:
    """Number of rows in a table — a cheap in-database COUNT(*), no data materialized.

    Use this instead of `profile` when you only need the row count (e.g. to size a
    table before an operation); it stays fast on arbitrarily large tables.
    """
    return {"table": table, "n_rows": _get(session_key).table(table).count_rows()}


@mcp.tool()
def count_non_null(session_key: str, table: str, column: str) -> dict:
    """Number of non-NULL (non-NaN) values in a column — an in-database COUNT(col).

    Returns the non-null count plus the row total and derived null count, all from
    a cheap COUNT with no data materialized. Fast on arbitrarily large tables.
    """
    t = _get(session_key).table(table)
    n_rows = t.count_rows()
    n_non_null = t.count_non_null(column)
    return {
        "table": table,
        "column": column,
        "n_non_null": n_non_null,
        "n_rows": n_rows,
        "n_null": n_rows - n_non_null,
    }


@mcp.tool()
def profile(session_key: str, table: str) -> dict:
    """Profile every column of a table: type, missingness, cardinality, distribution."""
    return _result(_get(session_key).table(table).profile())


@mcp.tool()
def detect_outliers(session_key: str, table: str, column: str) -> dict:
    """Flag outliers in a numeric column (IQR + z-score) and write the flags back as a column."""
    return _result(_get(session_key).table(table).detect_outliers(column))


@mcp.tool()
def analyze_association(session_key: str, table: str, col_a: str, col_b: str) -> dict:
    """Test the association between two columns; the test is chosen from the dtype pair."""
    return _result(_get(session_key).table(table).analyze_association(col_a, col_b))


@mcp.tool()
def association_matrix(session_key: str, table: str) -> dict:
    """Pairwise association strength across all column pairs of a table."""
    return _result(_get(session_key).table(table).association_matrix())


# --------------------------------------------------------------------------- #
# feature computation: build new model-eligible columns from existing ones
# --------------------------------------------------------------------------- #

@mcp.tool()
def combine_columns(
    session_key: str, table: str, col_a: str, col_b: str, op: str, name: str | None = None
) -> dict:
    """Create a feature by combining two numeric columns with an arithmetic op.

    `op` is one of: add, subtract, multiply, divide, ratio. Division-by-zero
    becomes NaN. This is the primitive for most domain features — e.g.
    density = mass / volume: you supply the columns and the op, the arithmetic is
    generic. The new column is written back and is eligible for modelling.
    """
    return _result(_get(session_key).table(table).combine_columns(col_a, col_b, op, name))


@mcp.tool()
def transform_column(
    session_key: str, table: str, column: str, func: str, name: str | None = None
) -> dict:
    """Create a feature by applying a math transform to one numeric column.

    `func` is one of: log, log1p, sqrt, square, reciprocal, abs, zscore. Values
    outside a transform's domain (e.g. log of a non-positive) become NaN. Use log
    to tame skew, zscore to standardise, etc.
    """
    return _result(_get(session_key).table(table).transform_column(column, func, name))


@mcp.tool()
def bin_column(
    session_key: str,
    table: str,
    column: str,
    n_bins: int = 4,
    strategy: str = "quantile",
    name: str | None = None,
) -> dict:
    """Discretise a numeric column into ordinal bins (a categorical feature).

    `strategy` = "quantile" (equal-frequency) or "uniform" (equal-width). The new
    column holds 0-based integer bin indices.
    """
    return _result(_get(session_key).table(table).bin_column(column, n_bins, strategy, name))


@mcp.tool()
def expand_datetime(
    session_key: str, table: str, column: str, parts: list[str] | None = None
) -> dict:
    """Expand a datetime column into calendar-component features.

    `parts` (default: year, month, dayofweek, is_weekend) is any subset of: year,
    quarter, month, week, day, dayofweek, dayofyear, hour, is_weekend,
    is_month_start, is_month_end. Each becomes `<column>_<part>`.
    """
    return _result(_get(session_key).table(table).expand_datetime(column, parts))


@mcp.tool()
def group_aggregate(
    session_key: str,
    table: str,
    group_by: str,
    value: str,
    agg: str = "mean",
    name: str | None = None,
    add_deviation: bool = False,
) -> dict:
    """Aggregate `value` within each `group_by` category, broadcast back to rows.

    Every row receives its group's statistic (e.g. each order gets its customer's
    mean spend) — a strong relational feature. `agg` is one of mean, sum, min,
    max, std, median, count. With `add_deviation=True`, also writes
    `<value>_dev_from_<group_by>` = value − group mean.
    """
    return _result(
        _get(session_key).table(table).group_aggregate(group_by, value, agg, name, add_deviation)
    )


@mcp.tool()
def row_aggregate(
    session_key: str, table: str, columns: list[str], agg: str = "sum", name: str | None = None
) -> dict:
    """Aggregate several numeric columns across each row into one feature.

    `agg` is one of mean, sum, min, max, std, median, count (count = number of
    non-null inputs). The generic form of a total like "total atom count" from
    per-element count columns.
    """
    return _result(_get(session_key).table(table).row_aggregate(columns, agg, name))


@mcp.tool()
def normalize_fractions(
    session_key: str, table: str, columns: list[str], suffix: str = "_frac"
) -> dict:
    """Turn a set of count/amount columns into per-row fractions of their total.

    Each `<col>` becomes `<col><suffix>` = col / (row sum across the set), so the
    new columns sum to 1 per row. The generic form of composition fractions.
    """
    return _result(_get(session_key).table(table).normalize_fractions(columns, suffix))


@mcp.tool()
def compute_feature(session_key: str, table: str, name: str, expression: str) -> dict:
    """Create one feature column from a custom SQL scalar expression — the escape
    hatch when the fixed feature tools can't express what you need.

    `expression` is a DuckDB scalar expression over the table's columns, evaluated
    per row INSIDE the database (nothing is streamed to the app, so it scales to
    massive tables), and stored as a new model-eligible column `name`. Examples:
      - "mass / NULLIF(volume, 0)"
      - "CASE WHEN age >= 18 THEN 'adult' ELSE 'minor' END"
      - "avg(spend) OVER (PARTITION BY customer_id)"
      - "regexp_extract(email, '@(.*)$', 1)"

    Strictly feature generation: it must be a single scalar expression. Statement
    chaining, subqueries, DDL/DML, and file/catalog functions (read_csv, attach,
    install, ...) are rejected, and the expression must reference existing columns.
    """
    return _result(_get(session_key).table(table).compute_feature(name, expression))


# --------------------------------------------------------------------------- #
# clustering / dimensionality reduction
# --------------------------------------------------------------------------- #

@mcp.tool()
def cluster(session_key: str, table: str, n_clusters: int | None = None) -> dict:
    """Cluster rows (k-means; k auto-selected by silhouette if omitted) and write labels back."""
    return _result(_get(session_key).table(table).cluster(n_clusters))


@mcp.tool()
def profile_clusters(session_key: str, table: str) -> dict:
    """Characterize each cluster (requires cluster() to have been run first)."""
    return _result(_get(session_key).table(table).profile_clusters())


@mcp.tool()
def reduce_dimensions(session_key: str, table: str, method: str = "pca", n_components: int = 2) -> dict:
    """Reduce a table to a few components (pca/tsne/umap) and write them back as columns."""
    return _result(_get(session_key).table(table).reduce_dimensions(method, n_components))


# --------------------------------------------------------------------------- #
# supervised + interpretation
# --------------------------------------------------------------------------- #

@mcp.tool()
def train_classifier(
    session_key: str, table: str, target: str, name: str | None = None, backend: str = "gbt"
) -> dict:
    """Train a classifier on a table and persist it under `name` (default: target).

    backend: "gbt" (default gradient-boosted trees) or "tabicl" (TabICL v2
    foundation model — no per-task training, strong on small/medium tables,
    needs the optional `tabicl` dependency).
    """
    return _train(session_key, table, target, name, "classification", backend)


@mcp.tool()
def train_regressor(
    session_key: str, table: str, target: str, name: str | None = None, backend: str = "gbt"
) -> dict:
    """Train a regressor on a table and persist it under `name` (default: target).

    backend: "gbt" (default gradient-boosted trees) or "tabicl" (TabICL v2
    foundation model — needs the optional `tabicl` dependency).
    """
    return _train(session_key, table, target, name, "regression", backend)


def _train(
    session_key: str, table: str, target: str, name: str | None, task: str, backend: str = "gbt"
) -> dict:
    session = _get(session_key)
    handle = session.table(table)
    model_name = name or target
    if task == "classification":
        model = handle.train_classifier(target, name=model_name, backend=backend)
    else:
        model = handle.train_regressor(target, name=model_name, backend=backend)
    if isinstance(model, Result):  # honesty seam declined training — surface it, don't save
        return _result(model)
    persistence.save_model(session, table, model_name, model)
    return {"model_name": model_name, "table": table, "target": target, "task": task,
            "backend": backend, "features": model._feature_names}


@mcp.tool()
def evaluate(session_key: str, table: str, model_name: str) -> dict:
    """Evaluate a trained model on its held-out test split."""
    return _result(_get(session_key).table(table).evaluate(model_name))


@mcp.tool()
def feature_importance(session_key: str, table: str, model_name: str) -> dict:
    """Permutation feature importance for a trained model."""
    return _result(_get(session_key).table(table).feature_importance(model_name))


@mcp.tool()
def add_predictions(session_key: str, table: str, model_name: str, column_name: str | None = None) -> dict:
    """Write a trained model's predictions back onto the table as a new column."""
    return _result(_get(session_key).table(table).add_predictions(model_name, column_name))


@mcp.tool()
def explain_prediction(session_key: str, table: str, model_name: str, row_index: int = 0) -> dict:
    """Explain a single prediction with SHAP; row_index is the 0-based table row."""
    handle = _get(session_key).table(table)
    row = handle.get_frame().iloc[int(row_index)].to_dict()
    return _result(handle.explain_prediction(model_name, row))


# --------------------------------------------------------------------------- #
# time series
# --------------------------------------------------------------------------- #

@mcp.tool()
def decompose(session_key: str, table: str, time_column: str, value_column: str) -> dict:
    """Decompose a time series into trend / seasonality / residual."""
    return _result(_get(session_key).table(table).decompose(time_column, value_column))


@mcp.tool()
def forecast(session_key: str, table: str, time_column: str, value_column: str, horizon: int = 10) -> dict:
    """Forecast a time series forward `horizon` steps (ARIMA)."""
    return _result(_get(session_key).table(table).forecast(time_column, value_column, horizon))


@mcp.tool()
def detect_changepoints(
    session_key: str, table: str, time_column: str, value_column: str, penalty: float = 10.0
) -> dict:
    """Detect points where a time series shifts behaviour (ruptures PELT).

    Needs the optional `insights` extra. Higher `penalty` = fewer changepoints.
    """
    return _result(_get(session_key).table(table).detect_changepoints(time_column, value_column, penalty))


# --------------------------------------------------------------------------- #
# insight primitives
# --------------------------------------------------------------------------- #

@mcp.tool()
def explain_metric(session_key: str, table: str, target: str, max_depth: int = 3) -> dict:
    """Explain a metric: ranked drivers + interpretable segment rules (shallow tree)."""
    return _result(_get(session_key).table(table).explain_metric(target, max_depth))


@mcp.tool()
def market_basket(
    session_key: str,
    table: str,
    transaction_column: str,
    item_column: str,
    min_support: float = 0.01,
    min_confidence: float = 0.2,
    max_rules: int = 50,
) -> dict:
    """Association-rule mining ("buy X → also buy Y"). Needs the optional `insights` extra."""
    return _result(_get(session_key).table(table).market_basket(
        transaction_column, item_column, min_support, min_confidence, max_rules))


@mcp.tool()
def causal_effect(
    session_key: str,
    table: str,
    treatment: str,
    outcome: str,
    confounders: list[str] | None = None,
) -> dict:
    """Estimate the causal effect of `treatment` on `outcome` (DoWhy backdoor).

    Needs the optional `insights` extra. Defaults confounders to all other features.
    """
    return _result(_get(session_key).table(table).causal_effect(treatment, outcome, confounders))


@mcp.tool()
def rfm(session_key: str, table: str, customer_column: str, date_column: str, monetary_column: str) -> dict:
    """RFM quintile segmentation of customers (Champions, At Risk, ...)."""
    return _result(_get(session_key).table(table).rfm(customer_column, date_column, monetary_column))


@mcp.tool()
def retention_cohorts(session_key: str, table: str, customer_column: str, date_column: str) -> dict:
    """Monthly retention matrix: first-purchase cohort × months-since."""
    return _result(_get(session_key).table(table).retention_cohorts(customer_column, date_column))


@mcp.tool()
def compare_periods(
    session_key: str, table: str, time_column: str, value_column: str, split: str | None = None
) -> dict:
    """Compare a metric before vs after a cut date (means, % change, significance)."""
    return _result(_get(session_key).table(table).compare_periods(time_column, value_column, split))


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
