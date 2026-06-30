"""Structured return contract for all analytics functions.

Note: TrainedModel (in supervised.py) is a *separate* callable type, not a Result.
It bundles fitted preprocessing and exposes .predict() — it is not an inert data
container like Result.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Result:
    """Base structured return for every analytics function.

    Two audiences read this: a human at a REPL (via __repr__) and, later, an
    orchestrating agent (via addressable fields). Keep fields explicit.
    """
    method: str                       # what was actually run/chosen
    summary: str = ""                 # one-line plain-language summary
    values: dict[str, Any] = field(default_factory=dict)  # statistics, scores, etc.
    metadata: dict[str, Any] = field(default_factory=dict)  # assumptions, params used
    artifact: Any = None              # optional raw object (model, fitted transform)

    def __repr__(self) -> str:        # readable for humans
        return f"<Result method={self.method!r} summary={self.summary!r}>"
