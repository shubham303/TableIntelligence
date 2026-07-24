"""Client for the Table Intelligence website APIs (reports, folders, outreach).

The MCP server holds no user data — it calls the website (the control plane) over
HTTP with the user's API key. Configure with:
  ``TABINT_CONTROL_PLANE_URL``  base URL of the site (default https://shubhamrandive.com)
  ``TABINT_API_KEY``            the user's key (from the website after signup)

The API key is sent in the ``x-api-key`` header (BetterAuth's apiKey plugin
default). Browser sessions use ``Authorization: Bearer <jwt>`` instead — the
two credential types are intentionally distinguished at the wire level.

Stdlib only. Returns the API's JSON; on an HTTP error it returns the error body so
the agent can relay a useful message (e.g. an upgrade prompt) instead of crashing.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

_DEFAULT = "https://shubhamrandive.com"
_TIMEOUT = 15


def _base() -> str:
    return (os.environ.get("TABINT_CONTROL_PLANE_URL") or _DEFAULT).rstrip("/")


def _key() -> str:
    return os.environ.get("TABINT_API_KEY", "").strip()


def configured() -> bool:
    return bool(_key())


def _request(method: str, path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        f"{_base()}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "x-api-key": _key()},
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # surface the API's error JSON
        try:
            return json.loads(exc.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            return {"error": f"http_{exc.code}"}
    except (urllib.error.URLError, OSError) as exc:
        return {"error": "unreachable", "message": f"Could not reach the website: {exc}"}


def save_report(title: str, content: str, folder_id: str | None = None,
                metadata: dict | None = None) -> dict:
    return _request("POST", "/api/reports",
                    {"title": title, "content": content, "folder_id": folder_id,
                     "metadata": metadata})


def list_reports(folder_id: str | None = None) -> dict:
    q = f"?folder={folder_id}" if folder_id else ""
    return _request("GET", f"/api/reports{q}")


def get_report(report_id: str) -> dict:
    return _request("GET", f"/api/reports/{report_id}")


def create_folder(name: str) -> dict:
    return _request("POST", "/api/folders", {"name": name})


def list_folders() -> dict:
    return _request("GET", "/api/folders")


# --------------------------------------------------------------------------- #
# outreach connector — templates, campaigns, emails, received (data/CRUD only)
# --------------------------------------------------------------------------- #

def _qs(params: dict) -> str:
    items = [(k, v) for k, v in params.items() if v not in (None, "")]
    return ("?" + urllib.parse.urlencode(items)) if items else ""


# templates
def create_template(title: str, prompt: str, status: str = "active") -> dict:
    return _request("POST", "/api/outreach/templates", {"title": title, "prompt": prompt, "status": status})

def list_templates(status: str | None = None, frm: str | None = None, to: str | None = None) -> dict:
    return _request("GET", "/api/outreach/templates" + _qs({"status": status, "from": frm, "to": to}))

def get_template(template_id: str) -> dict:
    return _request("GET", f"/api/outreach/templates/{template_id}")

def update_template(template_id: str, fields: dict) -> dict:
    return _request("PATCH", f"/api/outreach/templates/{template_id}", fields)

def delete_template(template_id: str) -> dict:
    return _request("DELETE", f"/api/outreach/templates/{template_id}")


# campaigns
def setup_campaign(template_id: str, title: str | None = None) -> dict:
    return _request("POST", "/api/outreach/campaigns", {"template_id": template_id, "title": title})

def get_campaign(campaign_id: str) -> dict:
    return _request("GET", f"/api/outreach/campaigns/{campaign_id}")

def list_campaigns(status: str | None = None, template_id: str | None = None,
                   frm: str | None = None, to: str | None = None) -> dict:
    return _request("GET", "/api/outreach/campaigns" + _qs(
        {"status": status, "template_id": template_id, "from": frm, "to": to}))


# emails (prospect + drafted email)
def add_email(campaign_id: str, recipients, subject: str, body: str,
              details=None, email_ids=None) -> dict:
    return _request("POST", "/api/outreach/emails", {
        "campaign_id": campaign_id, "recipients": recipients, "subject": subject,
        "body": body, "details": details, "email_ids": email_ids})

def list_emails(campaign_id: str, status: str | None = None) -> dict:
    return _request("GET", "/api/outreach/emails" + _qs({"campaign_id": campaign_id, "status": status}))


def ready_emails(campaign_id: str) -> dict:
    """Emails in a campaign that still need sending — every email whose status is
    not 'sent' (i.e. 'draft' or 'failed'). Filters client-side on top of
    list_emails; the API's status values are 'draft' | 'sent' | 'failed'."""
    res = list_emails(campaign_id)
    if isinstance(res, dict) and isinstance(res.get("emails"), list):
        res = dict(res)
        res["emails"] = [e for e in res["emails"] if e.get("status") != "sent"]
    return res

def get_email(email_id: str) -> dict:
    return _request("GET", f"/api/outreach/emails/{email_id}")

def update_email(email_id: str, fields: dict) -> dict:
    return _request("PATCH", f"/api/outreach/emails/{email_id}", fields)

def delete_email(email_id: str) -> dict:
    return _request("DELETE", f"/api/outreach/emails/{email_id}")


# received emails (global to the user)
def save_received(sender: str, subject: str, body: str, received_at: str | None = None) -> dict:
    return _request("POST", "/api/outreach/received",
                    {"sender": sender, "subject": subject, "body": body, "received_at": received_at})

def list_received() -> dict:
    return _request("GET", "/api/outreach/received")


# --------------------------------------------------------------------------- #
# social connector — templates, campaigns, search targets, posts, feedback,
# template-change proposals. Data/CRUD only. The agent never scrapes or posts;
# it stores templates/campaigns, emits SEARCH SPECS (the harness runs the
# reads), stores drafted posts + replies, and captures feedback. Mirrors the
# outreach connector.
# --------------------------------------------------------------------------- #

# templates
def social_create_template(title: str, prompt: str, status: str = "active") -> dict:
    return _request("POST", "/api/social/templates",
                    {"title": title, "prompt": prompt, "status": status})

def social_list_templates(status: str | None = None, frm: str | None = None,
                          to: str | None = None) -> dict:
    return _request("GET", "/api/social/templates" + _qs({"status": status, "from": frm, "to": to}))

def social_get_template(template_id: str) -> dict:
    return _request("GET", f"/api/social/templates/{template_id}")

def social_update_template(template_id: str, fields: dict) -> dict:
    return _request("PATCH", f"/api/social/templates/{template_id}", fields)

def social_delete_template(template_id: str) -> dict:
    return _request("DELETE", f"/api/social/templates/{template_id}")


# campaigns (setup freezes the template prompt into the campaign)
def social_setup_campaign(template_id: str, title: str | None = None) -> dict:
    return _request("POST", "/api/social/campaigns",
                    {"template_id": template_id, "title": title})

def social_get_campaign(campaign_id: str) -> dict:
    return _request("GET", f"/api/social/campaigns/{campaign_id}")

def social_list_campaigns(status: str | None = None, template_id: str | None = None,
                          frm: str | None = None, to: str | None = None) -> dict:
    return _request("GET", "/api/social/campaigns" + _qs(
        {"status": status, "template_id": template_id, "from": frm, "to": to}))


# search targets — structured SEARCH SPECS the harness runs (agent does not scrape)
def social_add_search_target(campaign_id: str, platform: str, search_type: str,
                             queries: list, scopes=None, recency: str = "7d",
                             keywords=None, max_results: int = 15) -> dict:
    return _request("POST", "/api/social/search-targets", {
        "campaign_id": campaign_id, "platform": platform, "search_type": search_type,
        "queries": queries, "scopes": scopes, "recency": recency,
        "keywords": keywords, "max_results": max_results,
    })

def social_list_search_targets(campaign_id: str, platform: str | None = None,
                               status: str | None = None) -> dict:
    return _request("GET", "/api/social/search-targets" + _qs(
        {"campaign_id": campaign_id, "platform": platform, "status": status}))

def social_update_search_target(search_target_id: str, fields: dict) -> dict:
    return _request("PATCH", f"/api/social/search-targets/{search_target_id}", fields)

def social_delete_search_target(search_target_id: str) -> dict:
    return _request("DELETE", f"/api/social/search-targets/{search_target_id}")


# posts — unified author + reply content
def social_add_post(campaign_id: str, platform: str, kind: str, content: str,
                    content_format: str = "text", target_url=None,
                    target_kind=None, target_title=None, target_author=None,
                    notes=None) -> dict:
    return _request("POST", "/api/social/posts", {
        "campaign_id": campaign_id, "platform": platform, "kind": kind,
        "content": content, "content_format": content_format,
        "target_url": target_url, "target_kind": target_kind,
        "target_title": target_title, "target_author": target_author, "notes": notes,
    })

def social_list_posts(campaign_id: str, status: str | None = None,
                      platform: str | None = None, kind: str | None = None) -> dict:
    return _request("GET", "/api/social/posts" + _qs(
        {"campaign_id": campaign_id, "status": status, "platform": platform, "kind": kind}))

def social_get_post(post_id: str) -> dict:
    return _request("GET", f"/api/social/posts/{post_id}")

def social_update_post(post_id: str, fields: dict) -> dict:
    return _request("PATCH", f"/api/social/posts/{post_id}", fields)

def social_delete_post(post_id: str, reason: str | None = None) -> dict:
    return _request("DELETE", f"/api/social/posts/{post_id}",
                    {"reason": reason} if reason else None)


# feedback — rejections + notes (the agent reads before each run)
def social_add_feedback(campaign_id: str, kind: str, reason: str,
                        note: str | None = None, post_id: str | None = None) -> dict:
    return _request("POST", "/api/social/feedback", {
        "campaign_id": campaign_id, "kind": kind, "reason": reason,
        "note": note, "post_id": post_id,
    })

def social_list_feedback(campaign_id: str | None = None,
                         kind: str | None = None) -> dict:
    return _request("GET", "/api/social/feedback" + _qs(
        {"campaign_id": campaign_id, "kind": kind}))

def social_delete_feedback(feedback_id: str) -> dict:
    return _request("DELETE", f"/api/social/feedback/{feedback_id}")


# template-change proposals — durable feedback becomes an approved patch
def social_propose_template_change(template_id: str, change_kind: str,
                                   rationale: str, proposed_patch: str,
                                   source_feedback_ids=None) -> dict:
    return _request("POST", "/api/social/template-changes", {
        "template_id": template_id, "change_kind": change_kind,
        "rationale": rationale, "proposed_patch": proposed_patch,
        "source_feedback_ids": source_feedback_ids,
    })

def social_list_template_changes(template_id: str | None = None,
                                 status: str | None = None) -> dict:
    return _request("GET", "/api/social/template-changes" + _qs(
        {"template_id": template_id, "status": status}))

def social_update_template_change(change_id: str, status: str,
                                 decision_note: str | None = None) -> dict:
    return _request("PATCH", f"/api/social/template-changes/{change_id}", {
        "status": status, "decision_note": decision_note})

def social_apply_template_change(change_id: str) -> dict:
    return _request("POST", f"/api/social/template-changes/{change_id}/apply")
