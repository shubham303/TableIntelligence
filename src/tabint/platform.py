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
# outreach — prompts, prospects, and sending (the outreach connector)
# --------------------------------------------------------------------------- #

def list_outreach_prompts() -> dict:
    return _request("GET", "/api/outreach/prompts")


def create_outreach_prompt(name: str, body: str) -> dict:
    return _request("POST", "/api/outreach/prompts", {"name": name, "body": body})


def update_outreach_prompt(prompt_id: str, name: str, body: str) -> dict:
    return _request("PATCH", f"/api/outreach/prompts/{prompt_id}", {"name": name, "body": body})


def delete_outreach_prompt(prompt_id: str) -> dict:
    return _request("DELETE", f"/api/outreach/prompts/{prompt_id}")


def list_prospects(status: str | None = None) -> dict:
    q = f"?status={status}" if status else ""
    return _request("GET", f"/api/outreach/prospects{q}")


def create_prospects(prospects: list[dict]) -> dict:
    """Create one or many prospects in a single call."""
    return _request("POST", "/api/outreach/prospects", {"prospects": prospects})


def get_prospect(prospect_id: str) -> dict:
    return _request("GET", f"/api/outreach/prospects/{prospect_id}")


def update_prospect(prospect_id: str, fields: dict) -> dict:
    return _request("PATCH", f"/api/outreach/prospects/{prospect_id}", fields)


def delete_prospect(prospect_id: str) -> dict:
    return _request("DELETE", f"/api/outreach/prospects/{prospect_id}")
