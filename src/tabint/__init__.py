"""tabint — a deterministic, reproducible intelligence layer for single-table data.

Public API is intentionally small. See docs/architecture.md for the design and
docs/roadmap.md for what's implemented vs. planned.
"""
from tabint.session import Session
from tabint.results import Result
from tabint.workspace import Workspace, Table
from tabint.relationships import RelationshipGraph, Relationship
from tabint import persistence

__all__ = [
    "Session", "Result", "Workspace", "Table",
    "RelationshipGraph", "Relationship", "persistence",
]
__version__ = "0.1.0"
