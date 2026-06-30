"""In-memory job registry for the slow-lane job model.

Fast-lane / slow-lane split: quick operations (descriptive stats, association
tests, PCA, fast models) return inline. Genuinely slow operations (AutoGluon,
exhaustive hyperparameter search, O(n²) methods on large data) run as jobs.
A job has an id, a status, a result, and an error. On completion, slow-lane
jobs write their results back as columns so querying them afterward is fast again.

The split is driven by estimated cost (≈ rows × features × algorithm factor),
not a static per-algorithm label.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


JobStatus = Literal["running", "done", "failed"]


@dataclass
class Job:
    """A single slow-lane job.

    Attributes:
        id: Unique identifier for this job.
        status: Current state of the job.
        result: The Result object when status is "done"; None otherwise.
        error: Error message when status is "failed"; None otherwise.
    """
    id: str
    status: JobStatus = "running"
    result: Any = None
    error: str | None = None


class JobRegistry:
    """In-memory registry of all slow-lane jobs in a session."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def register(self, job_id: str) -> Job:
        """Register a new job and return it.

        Args:
            job_id: Unique identifier for the job.

        Returns:
            A new Job with status "running".
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def get(self, job_id: str) -> Job:
        """Retrieve a job by id.

        Args:
            job_id: The job's unique identifier.

        Returns:
            The Job, or raises KeyError if not found.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def complete(self, job_id: str, result: Any) -> None:
        """Mark a job as done with its result.

        Args:
            job_id: The job's unique identifier.
            result: The Result object produced by the job.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def fail(self, job_id: str, error: str) -> None:
        """Mark a job as failed with an error message.

        Args:
            job_id: The job's unique identifier.
            error: Description of what went wrong.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")
