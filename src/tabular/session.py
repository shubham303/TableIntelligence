"""Session — thin state holder that delegates to the analytics layer.

This class is deliberately thin: it owns state (the store, registered models,
job registry) and delegates all computation to the analytics modules. It contains
no algorithms.

Note: predict() lives on the returned TrainedModel, NOT on Session. Session keeps
a registry of models (self.models[name]) so the agent can reference one by name.
"""
from __future__ import annotations

from typing import Any

from .store import Store


class Session:
    """State holder for a single-table analysis session.

    Construct via Session.load(path). All analytics methods delegate to the
    analytics layer — every method raises NotImplementedError in V0.
    """

    def __init__(self) -> None:
        self._store: Any = None
        self.models: dict[str, Any] = {}
        self._jobs: Any = None

    @classmethod
    def load(cls, path: str) -> "Session":
        """Load a CSV file into a new Session.

        Args:
            path: Path to the CSV file to load.

        Returns:
            A new Session with the table loaded.
        """
        session = cls()
        session._store = Store.for_csv(path)
        return session

    def profile(self) -> Any:
        """Profile every column: type, distribution, missingness, cardinality, range.

        Returns:
            Result with per-column statistics.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def detect_outliers(self, column: str) -> Any:
        """Detect outliers in a column using IQR and z-score flags.

        Args:
            column: Name of the column to analyze.

        Returns:
            Result with outlier flags and thresholds.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def analyze_association(self, col_a: str, col_b: str) -> Any:
        """Analyze the association between two columns using dtype-routed test selection.

        The test is selected automatically based on the dtype pair:
        - continuous × continuous → Pearson (normal) / Spearman
        - categorical × continuous → t-test / ANOVA / Kruskal-Wallis + effect size
        - categorical × categorical → chi-square / Fisher + Cramér's V

        Args:
            col_a: Name of the first column.
            col_b: Name of the second column.

        Returns:
            Result with the chosen test, statistic, p-value, and effect size.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def association_matrix(self) -> Any:
        """Compute pairwise associations across all column pairs.

        Returns:
            Result with a matrix of association measures, one per dtype-appropriate metric.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def cluster(self, n_clusters: int | None = None) -> Any:
        """Cluster rows and write cluster labels back as a column.

        Args:
            n_clusters: Number of clusters. If None, selected automatically via silhouette.

        Returns:
            Result with cluster labels, silhouette score, and cluster sizes.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def profile_clusters(self) -> Any:
        """Characterize each cluster in plain-language terms.

        Requires cluster() to have been called first (labels column must exist).

        Returns:
            Result with per-cluster summaries.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def train_classifier(self, target: str, name: str | None = None) -> Any:
        """Train a classification model on the loaded table.

        Args:
            target: Name of the target column.
            name: Optional name to register the model under in self.models.

        Returns:
            TrainedModel with bundled preprocessing and .predict() / .predict_proba().
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def train_regressor(self, target: str, name: str | None = None) -> Any:
        """Train a regression model on the loaded table.

        Args:
            target: Name of the target column.
            name: Optional name to register the model under in self.models.

        Returns:
            TrainedModel with bundled preprocessing and .predict().
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def evaluate(self, model_name: str) -> Any:
        """Evaluate a trained model with a full metric set.

        Args:
            model_name: Key in self.models.

        Returns:
            Result with metrics, confusion matrix, and evaluation parameters.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def feature_importance(self, model_name: str) -> Any:
        """Compute feature importance for a trained model.

        Args:
            model_name: Key in self.models.

        Returns:
            Result with gain-based and/or permutation importance scores.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def reduce_dimensions(self, method: str = "pca", n_components: int = 2) -> Any:
        """Reduce dimensionality of the table.

        Args:
            method: One of "pca", "tsne", "umap".
            n_components: Number of output dimensions.

        Returns:
            Result with transformed coordinates written back as columns.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def add_predictions(self, model_name: str, column_name: str | None = None) -> Any:
        """Write model predictions back as a new column.

        Args:
            model_name: Key in self.models.
            column_name: Name for the new predictions column. Defaults to f"{model_name}_pred".

        Returns:
            Result confirming the column was written.
        """
        raise NotImplementedError("planned: see docs/roadmap.md")

    def run_sql(self, query: str) -> Any:
        """Run a SQL query against the loaded table.

        Args:
            query: SQL query string. The table is accessible as 'data'.

        Returns:
            Result with query output as a DataFrame.
        """
        return self._store.run_sql(query)
