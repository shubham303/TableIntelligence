"""Shared JSON serialization for the CLI and MCP surfaces.

Both front-ends must turn Result objects (and arbitrary values/metadata dicts that
may contain numpy scalars or NaN) into strict-JSON-safe structures. Keeping that in
one place means the two surfaces never diverge on how a result is rendered.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np


def jsonable(obj: Any) -> Any:
    """Recursively coerce numpy scalars, NaN, and ±Infinity into JSON-safe values.

    NaN and infinities are not valid JSON (RFC 8259) and are rejected by strict
    parsers (Node, jq, Go, Rust), so they become null — an agent must never get a
    ``0``-exit success that it then fails to parse.
    """
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, np.generic):
        obj = obj.item()
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def result_dict(res: Any) -> dict:
    """Render a Result as a plain JSON dict (dropping any non-serializable artifact)."""
    return {
        "method": res.method,
        "summary": res.summary,
        "values": jsonable(res.values),
        "metadata": jsonable(res.metadata),
    }
