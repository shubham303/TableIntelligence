"""Clustering family.

Planned functions: cluster, profile_clusters.
Libraries (planned, not yet imported): scikit-learn.
"""
from __future__ import annotations

from typing import Any

# planned: from sklearn import cluster as sk_cluster
# planned: from sklearn.metrics import silhouette_score


def cluster(store: Any, n_clusters: int | None = None) -> Any:
    """Cluster table rows and write cluster labels back as a column.

    Scales features before clustering. If n_clusters is None, selects k
    automatically using the silhouette method (or elbow). Labels are written
    back to the store as a new column so follow-up queries become ordinary SQL.

    Args:
        store: The Store instance holding the table.
        n_clusters: Number of clusters. If None, selected automatically.

    Returns:
        Result with cluster labels, silhouette score, cluster sizes, and
        the algorithm and k chosen.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")


def profile_clusters(store: Any) -> Any:
    """Characterize each cluster in plain-language terms.

    Requires cluster() to have been called first so the cluster labels column
    exists in the store.

    Args:
        store: The Store instance holding the table (with cluster labels column).

    Returns:
        Result with per-cluster summaries: dominant feature values, size, and
        a plain-language description of what makes each cluster distinct.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
