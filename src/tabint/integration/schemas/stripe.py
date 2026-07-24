"""The normalization contract — the canonical table shapes every connector emits.

One contract, drawn before connector #2, so:
  * the 44 analytics tools consume any source uniformly (they see canonical columns);
  * a connector (built) or a first-party MCP server (delegated) only has to reach
    these shapes;
  * platform prompts can name real columns ("rfm on `payments`: customer_id, created_at,
    amount") that exist regardless of source.

A connector maps its raw objects to a DataFrame and calls ``conform(df, entity)`` to
guarantee the canonical columns, order, and dtypes. Extra columns are dropped; missing
ones are filled with nulls. Amounts are in major currency units (e.g. dollars, not
cents); timestamps are timezone-aware datetimes.
"""
from __future__ import annotations

import pandas as pd

# entity -> {canonical_column: dtype}  (dtype in {"str","float","bool","datetime"})
SCHEMAS: dict[str, dict[str, str]] = {
    "payments": {
        "id": "str",
        "created_at": "datetime",
        "amount": "float",
        "currency": "str",
        "customer_id": "str",
        "status": "str",
        "refunded": "bool",
        "description": "str",
    },
    "customers": {
        "id": "str",
        "created_at": "datetime",
        "email": "str",
        "country": "str",
        "delinquent": "bool",
    },
    "subscriptions": {
        "id": "str",
        "customer_id": "str",
        "status": "str",
        "created_at": "datetime",
        "current_period_end": "datetime",
        "canceled_at": "datetime",
        "plan_amount": "float",
        "interval": "str",
    },
    "invoices": {
        "id": "str",
        "customer_id": "str",
        "created_at": "datetime",
        "amount_paid": "float",
        "amount_due": "float",
        "status": "str",
    },
}


def entities() -> list[str]:
    return list(SCHEMAS)


def conform(df: pd.DataFrame, entity: str) -> pd.DataFrame:
    """Coerce ``df`` to the canonical schema for ``entity``: exact columns, order,
    and dtypes. Missing columns are added as null; extras are dropped. Idempotent."""
    if entity not in SCHEMAS:
        raise ValueError(f"Unknown canonical entity {entity!r}; known: {entities()}")
    schema = SCHEMAS[entity]
    out = df.copy() if df is not None else pd.DataFrame()
    for col, dtype in schema.items():
        if col not in out.columns:
            out[col] = pd.NA
        if dtype == "datetime":
            out[col] = pd.to_datetime(out[col], errors="coerce", utc=True)
        elif dtype == "float":
            out[col] = pd.to_numeric(out[col], errors="coerce")
        elif dtype == "bool":
            out[col] = out[col].astype("boolean")
        else:
            out[col] = out[col].astype("string")
    return out[list(schema.keys())]
