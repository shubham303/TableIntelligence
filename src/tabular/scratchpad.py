"""Per-session scratchpad — a plain-text notebook the agent writes as it works.

Deliberately dumb: one append-only text file per session at
``~/.tableintelligence/<session_id>.md``. The agent adds free-form English
whenever it wants (a finding, a thing it tried, a reminder); each chunk is stamped
with the date-time it was written. Reading returns the whole file; searching is a
simple case-insensitive substring match over chunks, grep-style.

This is the agent's own working memory — separate from the analysis data, and only
the agent touches it. No schema, no keys, no tags: just timestamped notes.

The file lives under the user's home dir, deliberately OUTSIDE any session
directory, so deleting a session never removes its notes — the record of what was
explored outlives the data. (Access via the CLI/MCP surfaces still requires a live
session; the file simply isn't tied to the session's on-disk lifecycle.)
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

_DIR = Path.home() / ".tableintelligence"

# Each chunk starts with a "## <date-time>" header; that's how chunks are delimited.
_HEADER_RE = re.compile(r"^## \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", re.MULTILINE)


def _safe(session_id: str) -> str:
    """Reduce a session id to a filesystem-safe stem (no path traversal)."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", session_id).strip("_")
    return cleaned or "session"


def _path(session_id: str) -> Path:
    """Path to the session's scratchpad file under ~/.tableintelligence/."""
    return _DIR / f"{_safe(session_id)}.md"


def add(session_id: str, text: str) -> str:
    """Append a date-time-stamped chunk of free-form text; return the timestamp."""
    _DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _path(session_id).open("a", encoding="utf-8") as f:
        f.write(f"## {stamp}\n{text.strip()}\n\n")
    return stamp


def read(session_id: str) -> str:
    """Return the whole scratchpad as text (empty string if nothing written yet)."""
    path = _path(session_id)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _chunks(content: str) -> list[str]:
    """Split the file back into its timestamped chunks."""
    starts = [m.start() for m in _HEADER_RE.finditer(content)]
    if not starts:
        return [content.strip()] if content.strip() else []
    bounds = starts + [len(content)]
    out = [content[bounds[i]:bounds[i + 1]].strip() for i in range(len(starts))]
    return [c for c in out if c]


def search(session_id: str, query: str) -> list[str]:
    """Return the chunks that contain ``query`` (case-insensitive substring, grep-like)."""
    q = query.lower()
    return [c for c in _chunks(read(session_id)) if q in c.lower()]
