"""End-to-end tests for the analytics families, driven through Session.

Each test loads a fixture into a temp-dir-backed store (so .tableint artifacts
never pollute the repo) with a cleared Store registry for isolation.
"""
import shutil

import pytest

from tabular import Result, Session


def _session(fixture: str, tmp_path) -> Session:
    src = f"tests/fixtures/{fixture}"
    dst = tmp_path / fixture
    shutil.copy(src, dst)
    return Session.load(str(dst))


def _columns(s: Session) -> list[str]:
    """Column names of the session's sole table (via its real name)."""
    return list(s.table(s.tables[0]).get_frame().columns)


def _first_row(s: Session) -> dict:
    """First row of the sole table as a dict."""
    return s.table(s.tables[0]).get_frame().iloc[0].to_dict()


# --------------------------------------------------------------------------- #
# association — the flagship routing
# --------------------------------------------------------------------------- #

class TestAssociation:
    def test_continuous_continuous_routes_to_correlation(self, tmp_path):
        s = _session("employees.csv", tmp_path)
        r = s.analyze_association("age", "salary")
        assert r.method in {"pearson", "spearman"}
        assert "effect_size" in r.values
        assert "p_value" in r.values

    def test_categorical_continuous_routes_to_group_test(self, tmp_path):
        s = _session("employees.csv", tmp_path)
        r = s.analyze_association("department", "salary")
        assert r.method in {"t_test", "anova", "mann_whitney", "kruskal_wallis"}
        assert r.metadata["effect_size_measure"] in {"eta_squared", "epsilon_squared"}

    def test_categorical_categorical_routes_to_chi_or_fisher(self, tmp_path):
        s = _session("employees.csv", tmp_path)
        r = s.analyze_association("department", "is_manager")
        assert r.method in {"chi_square", "fisher_exact"}
        assert r.metadata["effect_size_measure"] == "cramers_v"

    def test_effect_size_in_unit_range(self, tmp_path):
        s = _session("employees.csv", tmp_path)
        r = s.analyze_association("department", "is_manager")
        assert 0.0 <= r.values["effect_size"] <= 1.0

    def test_identifier_column_raises(self, tmp_path):
        s = _session("employees.csv", tmp_path)
        with pytest.raises(ValueError):
            s.analyze_association("employee_id", "salary")


# --------------------------------------------------------------------------- #
# descriptive
# --------------------------------------------------------------------------- #

class TestDescriptive:
    def test_profile_covers_all_columns(self, tmp_path):
        s = _session("employees.csv", tmp_path)
        r = s.profile()
        assert isinstance(r, Result)
        assert set(r.values) == {
            "employee_id", "name", "department", "age", "salary",
            "years_at_company", "is_manager", "performance_rating",
        }
        assert r.values["salary"]["type"] == "continuous"
        assert "mean" in r.values["salary"]

    def test_detect_outliers_writes_flag_column(self, tmp_path):
        s = _session("employees.csv", tmp_path)
        r = s.detect_outliers("salary")
        flag_col = r.metadata["flag_column"]
        cols = _columns(s)
        assert flag_col in cols
        assert r.values["n_outliers"] >= 0

    def test_detect_outliers_rejects_categorical(self, tmp_path):
        s = _session("employees.csv", tmp_path)
        with pytest.raises(ValueError):
            s.detect_outliers("department")

    def test_association_matrix_is_symmetric(self, tmp_path):
        s = _session("employees.csv", tmp_path)
        r = s.association_matrix()
        m = r.values["matrix"]
        cols = r.values["columns"]
        for a in cols:
            for b in cols:
                va, vb = m[a][b], m[b][a]
                if va is not None and vb is not None:
                    assert abs(va - vb) < 1e-9


# --------------------------------------------------------------------------- #
# clustering
# --------------------------------------------------------------------------- #

class TestClustering:
    def test_cluster_writes_label_column(self, tmp_path):
        s = _session("customers.csv", tmp_path)
        r = s.cluster(n_clusters=3)
        assert r.values["n_clusters"] == 3
        cols = _columns(s)
        assert "cluster" in cols

    def test_cluster_auto_selects_k(self, tmp_path):
        s = _session("customers.csv", tmp_path)
        r = s.cluster()
        assert 2 <= r.values["n_clusters"] <= 10
        assert r.metadata["k_selection"] == "silhouette"

    def test_profile_clusters_requires_labels(self, tmp_path):
        s = _session("customers.csv", tmp_path)
        with pytest.raises(ValueError):
            s.profile_clusters()

    def test_profile_clusters_after_cluster(self, tmp_path):
        s = _session("customers.csv", tmp_path)
        s.cluster(n_clusters=3)
        r = s.profile_clusters()
        assert len(r.values["clusters"]) == 3


# --------------------------------------------------------------------------- #
# supervised
# --------------------------------------------------------------------------- #

class TestSupervised:
    def test_train_classifier_registers_model(self, tmp_path):
        s = _session("loan_applications.csv", tmp_path)
        s.train_classifier("is_approved", name="approve")
        assert "approve" in s.models

    def test_evaluate_classifier_metrics(self, tmp_path):
        s = _session("loan_applications.csv", tmp_path)
        s.train_classifier("is_approved", name="approve")
        r = s.evaluate("approve")
        for metric in ("accuracy", "precision", "recall", "f1"):
            assert 0.0 <= r.values[metric] <= 1.0
        assert "confusion_matrix" in r.values

    def test_evaluate_regressor_metrics(self, tmp_path):
        s = _session("employees.csv", tmp_path)
        s.train_regressor("salary", name="sal")
        r = s.evaluate("sal")
        assert {"mae", "rmse", "r2"} <= set(r.values)

    def test_add_predictions_writes_column(self, tmp_path):
        s = _session("loan_applications.csv", tmp_path)
        s.train_classifier("is_approved", name="approve")
        s.add_predictions("approve", column_name="pred")
        cols = _columns(s)
        assert "pred" in cols

    def test_predict_on_new_row(self, tmp_path):
        s = _session("loan_applications.csv", tmp_path)
        model = s.train_classifier("is_approved", name="approve")
        row = _first_row(s)
        preds = model.predict(row)
        assert len(preds) == 1

    def test_evaluate_unknown_model_raises(self, tmp_path):
        s = _session("employees.csv", tmp_path)
        with pytest.raises(KeyError):
            s.evaluate("nope")


# --------------------------------------------------------------------------- #
# interpretation
# --------------------------------------------------------------------------- #

class TestInterpretation:
    def test_feature_importance_ranks_features(self, tmp_path):
        s = _session("loan_applications.csv", tmp_path)
        model = s.train_classifier("is_approved", name="approve")
        r = s.feature_importance("approve")
        imp = r.values["importances"]
        assert set(imp) == set(model._feature_names)
        # sorted descending
        vals = list(imp.values())
        assert vals == sorted(vals, reverse=True)

    def test_explain_prediction_returns_contributions(self, tmp_path):
        s = _session("loan_applications.csv", tmp_path)
        model = s.train_classifier("is_approved", name="approve")
        row = _first_row(s)
        r = s.explain_prediction("approve", row)
        assert set(r.values["contributions"]) == set(model._feature_names)
        assert "base_value" in r.values


# --------------------------------------------------------------------------- #
# dimensionality reduction
# --------------------------------------------------------------------------- #

class TestDimReduction:
    def test_pca_writes_components(self, tmp_path):
        s = _session("customers.csv", tmp_path)
        r = s.reduce_dimensions("pca", n_components=2)
        assert r.values["columns"] == ["pca_0", "pca_1"]
        cols = _columns(s)
        assert "pca_0" in cols and "pca_1" in cols
        assert len(r.values["explained_variance_ratio"]) == 2

    def test_tsne_writes_components(self, tmp_path):
        s = _session("customers.csv", tmp_path)
        r = s.reduce_dimensions("tsne", n_components=2)
        assert r.values["columns"] == ["tsne_0", "tsne_1"]

    def test_unknown_method_raises(self, tmp_path):
        s = _session("customers.csv", tmp_path)
        with pytest.raises(ValueError):
            s.reduce_dimensions("nope")


# --------------------------------------------------------------------------- #
# time series
# --------------------------------------------------------------------------- #

class TestTimeSeries:
    def test_decompose_returns_components(self, tmp_path):
        s = _session("monthly_sales.csv", tmp_path)
        r = s.decompose("month", "sales")
        assert {"trend", "seasonal", "residual"} <= set(r.values)
        assert len(r.values["trend"]) == 48

    def test_forecast_returns_horizon_points(self, tmp_path):
        s = _session("monthly_sales.csv", tmp_path)
        r = s.forecast("month", "sales", horizon=6)
        assert len(r.values["forecast"]) == 6
        assert len(r.values["lower"]) == 6
        assert len(r.values["upper"]) == 6
