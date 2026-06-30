"""tabular — a deterministic, reproducible intelligence layer for single-table data.

Public API is intentionally small. See docs/architecture.md for the design and
docs/roadmap.md for what's implemented vs. planned.
"""
from tabular.session import Session
from tabular.results import Result

__all__ = ["Session", "Result"]
__version__ = "0.0.0"
