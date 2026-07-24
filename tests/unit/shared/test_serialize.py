"""Tests for the serialize helpers — JSON-safe coercion.

Mirrors: src/tabint/shared/serialize.py
"""
import json

from tabint.shared.serialize import jsonable


def test_jsonable_handles_infinity():
    out = jsonable({"a": float("inf"), "b": float("-inf"), "c": float("nan"), "d": 1.5})
    assert out == {"a": None, "b": None, "c": None, "d": 1.5}
    json.loads(json.dumps(out))  # strict parse succeeds
