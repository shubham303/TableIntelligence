"""Slow-lane async runner.

Dispatches expensive operations as background jobs. When complete, the job
writes its results back as columns via store.write_back_column so follow-up
queries are fast again (they're just column reads at that point).
"""
from __future__ import annotations

from typing import Any, Callable


def run_async(
    fn: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    registry: Any,
    store: Any,
    job_id: str,
) -> str:
    """Dispatch a function to run as a background job.

    Args:
        fn: The analytics function to call asynchronously.
        args: Positional arguments to pass to fn.
        kwargs: Keyword arguments to pass to fn.
        registry: The JobRegistry to update with status and result.
        store: The Store to write results back to on completion.
        job_id: The unique job identifier (pre-registered in registry).

    Returns:
        The job_id, so the caller can poll status via registry.get(job_id).
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
