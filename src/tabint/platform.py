"""Client for the Table Intelligence website APIs (reports, folders).

The MCP server holds no user data — it calls the website (the control plane) over
HTTP with the user's API key. Configure with:
  ``TABINT_CONTROL_PLANE_URL``  base URL of the site (default https://shubhamrandive.com)
  ``TABINT_API_KEY``            the user's key (from the website after signup)

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
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {_key()}"},
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
