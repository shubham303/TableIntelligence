"""Operation identity and caching key computation.

Exists so expensive operations (slow-lane jobs like AutoGluon runs, large
clustering jobs) are never recomputed for the same inputs. An operation key
is a stable hash of the operation name, its parameters, and a fingerprint of
the columns it reads — same inputs always yield the same key.
"""
from __future__ import annotations

from typing import Any


def operation_key(name: str, params: dict[str, Any], column_fingerprint: str) -> str:
    """Compute a stable hash key for an operation and its inputs.

    Args:
        name: Operation name (e.g., "cluster", "train_classifier").
        params: Dict of parameters passed to the operation.
        column_fingerprint: A hash or digest of the relevant input columns.

    Returns:
        A stable hex-string key that uniquely identifies this operation + inputs.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
