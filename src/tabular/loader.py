"""CSV and DataFrame ingestion with initial dtype inference.

Responsible for reading raw files and producing a clean representation that
the Store can ingest. Dtype inference here is coarse (e.g., numeric vs. string);
fine-grained column classification (continuous / categorical / datetime / identifier)
is the responsibility of validation.dtypes.
"""
from __future__ import annotations

from typing import Any


def load(path: str) -> Any:
    """Load a CSV file and return it with inferred dtypes.

    Args:
        path: Path to the CSV file.

    Returns:
        A pandas DataFrame with dtypes inferred from the file content.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
