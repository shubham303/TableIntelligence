"""Operation identity and caching key computation.

Exists so expensive operations (slow-lane jobs like AutoGluon runs, large
clustering jobs) are never recomputed for the same inputs. An operation key
is a stable hash of the operation name, its parameters, and a fingerprint of
the columns it reads — same inputs always yield the same key.

Why SHA-256 over json.dumps?
- json.dumps with sort_keys=True gives a canonical, order-independent representation.
- SHA-256 is deterministic across Python restarts (unlike the built-in hash()).
- It's fast enough for a cache-key path that runs once per operation.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def _json_default(obj: Any) -> Any:
    """Coerce non-JSON-serializable types that appear in params dicts."""
    import numpy as np
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def operation_key(name: str, params: dict[str, Any], column_fingerprint: str) -> str:
    """Compute a stable hash key for an operation and its inputs.

    Args:
        name: Operation name (e.g., "cluster", "train_classifier").
        params: Dict of parameters passed to the operation. Values may be
            plain Python types or numpy scalars/arrays.
        column_fingerprint: A hex digest of the relevant input columns,
            produced by fingerprint_series or fingerprint_dataframe.

    Returns:
        A 64-character hex string that uniquely identifies this
        operation + parameters + input data combination.
    """
    payload = json.dumps(
        {"name": name, "params": params, "fingerprint": column_fingerprint},
        sort_keys=True,
        default=_json_default,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def fingerprint_series(series: Any) -> str:
    """Produce a stable hex digest for a single pandas Series.

    Uses pandas.util.hash_pandas_object for element-level, vectorized
    hashing, then feeds the ordered array of per-row hashes through SHA-256
    so that row order is preserved (sum would be commutative and lose order).

    Args:
        series: A pandas Series (the column to fingerprint).

    Returns:
        A 16-character hex string representing the column's content.
    """
    import pandas as pd
    hashes = pd.util.hash_pandas_object(series, index=False)
    return hashlib.sha256(hashes.values.tobytes()).hexdigest()[:16]


def fingerprint_dataframe(df: Any) -> str:
    """Produce a stable hex digest for an entire DataFrame.

    Hashes every row together so that adding, removing, reordering columns,
    or changing any value produces a different fingerprint.

    Args:
        df: A pandas DataFrame.

    Returns:
        A 16-character hex string representing the DataFrame's content.
    """
    import pandas as pd
    hashes = pd.util.hash_pandas_object(df, index=False)
    return hashlib.sha256(hashes.values.tobytes()).hexdigest()[:16]
