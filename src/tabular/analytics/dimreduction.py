"""Dimensionality reduction family.

Planned functions: reduce_dimensions.
Libraries (planned, not yet imported): scikit-learn (PCA, t-SNE), umap-learn (UMAP).
"""
from __future__ import annotations

from typing import Any

# planned: from sklearn.decomposition import PCA
# planned: from sklearn.manifold import TSNE
# planned: import umap


def reduce_dimensions(
    store: Any,
    method: str = "pca",
    n_components: int = 2,
) -> Any:
    """Reduce table dimensionality and write the components back as columns.

    Supports:
        "pca"  — linear, interpretable, fast. Components are written back as
                 pca_0, pca_1, ... columns.
        "tsne" — non-linear, good for cluster visualization. Slower; 2D only.
        "umap" — non-linear, preserves global structure better than t-SNE.

    Reduced coordinates are written back to the store as new columns so follow-up
    clustering on the reduced space becomes an ordinary query.

    Args:
        store: The Store instance holding the table.
        method: One of "pca", "tsne", "umap".
        n_components: Number of output dimensions (typically 2 for visualization).

    Returns:
        Result with the explained variance (PCA) or layout coordinates, and
        the column names written back.
    """
    raise NotImplementedError("planned: see docs/roadmap.md")
