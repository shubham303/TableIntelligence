"""End-to-end tests for the analytics families, driven through Session.

Each test loads a fixture into a temp-dir-backed Session (so .tableint artifacts
never pollute the repo) via the shared ``session_loader`` fixture.

Mirrors: src/tabint/analysis/session.py (the delegating surface), exercising
the algorithms under src/tabint/analysis/service/algorithms/.
"""
import pytest

from tabint import Result, Session


def _columns(s: Session) -> list[str]:
    """Column names of the session's sole table (via its real name)."""
    return list(s.table(s.tables[0]).get_frame().columns)


def _first_row(s: Session) -> dict:
    """First row of the sole table as a dict."""
    return s.table(s.tables[0]).get_frame().iloc[0].to_dict()


# --------------------------------------------------------------------------- #
# counts — cheap in-database row / non-null counts
# --------------------------------------------------------------------------- #

class TestCounts:
    def test_count_rows_matches_frame(self, session_loader):
        s = session_loader("employees.csv")
        t = s.table(s.tables[0])
        assert t.count_rows() == len(t.get_frame())

    def test_count_non_null_matches_frame(self, session_loader):
        s = session_loader("employees.csv")
        t = s.table(s.tables[0])
        frame = t.get_frame()
        for col in frame.columns:
            assert t.count_non_null(col) == int(frame[col].notna().sum())

    def test_count_non_null_unknown_column_raises(self, session_loader):
        s = session_loader("employees.csv")
        with pytest.raises(KeyError):
            s.table(s.tables[0]).count_non_null("does_not_exist")


# --------------------------------------------------------------------------- #
# association — the flagship routing
# --------------------------------------------------------------------------- #

class TestAssociation:
    def test_continuous_continuous_routes_to_correlation(self, session_loader):
        s = session_loader("employees.csv")
        r = s.analyze_association("age", "salary")
        assert r.method in {"pearson", "spearman"}
        assert "effect_size" in r.values
        assert "p_value" in r.values

    def test_categorical_continuous_routes_to_group_test(self, session_loader):
        s = session_loader("employees.csv")
        r = s.analyze_association("department", "salary")
        assert r.method in {"welch_t_test", "anova", "mann_whitney", "kruskal_wallis"}
        assert r.metadata["effect_size_measure"] in {"eta_squared", "epsilon_squared"}

    def test_categorical_categorical_routes_to_chi_or_fisher(self, session_loader):
        s = session_loader("employees.csv")
        r = s.analyze_association("department", "is_manager")
        assert r.method in {"chi_square", "fisher_exact"}
        assert r.metadata["effect_size_measure"] == "cramers_v"

    def test_effect_size_in_unit_range(self, session_loader):
        s = session_loader("employees.csv")
        r = s.analyze_association("department", "is_manager")
        assert 0.0 <= r.values["effect_size"] <= 1.0

    def test_identifier_column_raises(self, session_loader):
        s = session_loader("employees.csv")
        with pytest.raises(ValueError):
            s.analyze_association("employee_id", "salary")

    def test_two_normal_groups_use_welch_even_with_unequal_variance(self, tmp_path):
        # Welch's t-test does not assume equal variance, so unequal-variance but
        # normal 2-group data must stay parametric (not fall to Mann-Whitney).
        import csv

        import numpy as np
        from scipy import stats

        rng = np.random.default_rng(0)
        g1, g2 = rng.normal(50, 2, 60), rng.normal(52, 20, 60)
        p = tmp_path / "g.csv"
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["grp", "val"])
            w.writerows([["A", v] for v in g1] + [["B", v] for v in g2])
        s = Session.load(str(p))
        s.classify_categorical_as_nominal()  # mock the LLM step (grp is categorical)
        r = s.analyze_association("grp", "val")
        assert r.method == "welch_t_test"
        assert r.metadata["assumption_checks"]["equal_variance"] is False
        assert r.metadata["assumption_checks"]["parametric"] is True
        assert abs(r.values["p_value"] - stats.ttest_ind(g1, g2, equal_var=False).pvalue) < 1e-9


# --------------------------------------------------------------------------- #
# descriptive
# --------------------------------------------------------------------------- #

class TestDescriptive:
    def test_profile_covers_all_columns(self, session_loader):
        s = session_loader("employees.csv")
        r = s.profile()
        assert isinstance(r, Result)
        assert set(r.values) == {
            "employee_id", "name", "department", "age", "salary",
            "years_at_company", "is_manager", "performance_rating",
        }
        assert r.values["salary"]["type"] == "continuous"
        assert "mean" in r.values["salary"]

    def test_detect_outliers_writes_flag_column(self, session_loader):
        s = session_loader("employees.csv")
        r = s.detect_outliers("salary")
        flag_col = r.metadata["flag_column"]
        method_col = r.metadata["method_column"]
        cols = _columns(s)
        assert flag_col in cols
        assert method_col in cols
        assert r.values["n_outliers"] >= 0

        # The per-row method tag agrees with the boolean flag and only ever
        # names a method (or None), never an unexpected value.
        frame = s.run_sql(f'SELECT "{flag_col}", "{method_col}" FROM {s.tables[0]}')
        tagged = frame[frame[flag_col] == True][method_col]  # noqa: E712
        assert set(tagged.dropna().unique()) <= {"iqr", "zscore", "both"}
        assert tagged.notna().all()
        # Non-outlier rows carry no method.
        assert frame[frame[flag_col] == False][method_col].isna().all()  # noqa: E712

    def test_detect_outliers_rejects_categorical(self, session_loader):
        s = session_loader("employees.csv")
        with pytest.raises(ValueError):
            s.detect_outliers("department")

    def test_association_matrix_is_symmetric(self, session_loader):
        s = session_loader("employees.csv")
        r = s.association_matrix()
        m = r.values["matrix"]
        cols = r.values["columns"]
        for a in cols:
            for b in cols:
                va, vb = m[a][b], m[b][a]
                if va is not None and vb is not None:
                    assert abs(va - vb) < 1e-9

    def test_association_matrix_excludes_derived_columns(self, session_loader):
        s = session_loader("employees.csv")
        s.detect_outliers("salary")  # writes salary_is_outlier + _outlier_method
        cols = s.association_matrix().values["columns"]
        assert "salary_is_outlier" not in cols
        assert "salary_outlier_method" not in cols
        assert "salary" in cols  # the real variable stays


# --------------------------------------------------------------------------- #
# clustering
# --------------------------------------------------------------------------- #

class TestClustering:
    def test_cluster_writes_label_column(self, session_loader):
        s = session_loader("customers.csv")
        r = s.cluster(n_clusters=3)
        assert r.values["n_clusters"] == 3
        cols = _columns(s)
        assert "cluster" in cols

    def test_cluster_auto_selects_k(self, session_loader):
        s = session_loader("customers.csv")
        r = s.cluster()
        assert 2 <= r.values["n_clusters"] <= 10
        assert r.metadata["k_selection"] == "silhouette"

    def test_profile_clusters_requires_labels(self, session_loader):
        s = session_loader("customers.csv")
        with pytest.raises(ValueError):
            s.profile_clusters()

    def test_profile_clusters_after_cluster(self, session_loader):
        s = session_loader("customers.csv")
        s.cluster(n_clusters=3)
        r = s.profile_clusters()
        assert len(r.values["clusters"]) == 3


# --------------------------------------------------------------------------- #
# supervised
# --------------------------------------------------------------------------- #

class TestSupervised:
    def test_train_classifier_registers_model(self, session_loader):
        s = session_loader("loan_applications.csv")
        s.train_classifier("is_approved", name="approve")
        assert "approve" in s.models

    def test_evaluate_classifier_metrics(self, session_loader):
        s = session_loader("loan_applications.csv")
        s.train_classifier("is_approved", name="approve")
        r = s.evaluate("approve")
        for metric in ("accuracy", "precision", "recall", "f1"):
            assert 0.0 <= r.values[metric] <= 1.0
        assert "confusion_matrix" in r.values

    def test_evaluate_regressor_metrics(self, session_loader):
        s = session_loader("employees.csv")
        s.train_regressor("salary", name="sal")
        r = s.evaluate("sal")
        assert {"mae", "rmse", "r2"} <= set(r.values)

    def test_add_predictions_writes_column(self, session_loader):
        s = session_loader("loan_applications.csv")
        s.train_classifier("is_approved", name="approve")
        s.add_predictions("approve", column_name="pred")
        cols = _columns(s)
        assert "pred" in cols

    def test_predict_on_new_row(self, session_loader):
        s = session_loader("loan_applications.csv")
        model = s.train_classifier("is_approved", name="approve")
        row = _first_row(s)
        preds = model.predict(row)
        assert len(preds) == 1

    def test_evaluate_unknown_model_raises(self, session_loader):
        s = session_loader("employees.csv")
        with pytest.raises(KeyError):
            s.evaluate("nope")

    def test_default_backend_is_gbt(self, session_loader):
        s = session_loader("loan_applications.csv")
        model = s.train_classifier("is_approved", name="approve")
        assert model._backend == "gbt"
        r = s.evaluate("approve")
        assert r.metadata["backend"] == "gbt"

    def test_unknown_backend_raises(self, session_loader):
        s = session_loader("loan_applications.csv")
        with pytest.raises(ValueError, match="Unknown backend"):
            s.train_classifier("is_approved", name="approve", backend="bogus")

    def test_tabicl_backend_trains_or_reports_missing_dep(self, session_loader):
        """backend='tabicl' either trains (if installed) or raises a clear
        ImportError pointing at the optional extra — never a cryptic failure."""
        s = session_loader("loan_applications.csv")
        try:
            model = s.train_classifier("is_approved", name="approve", backend="tabicl")
        except ImportError as exc:
            assert "tabicl" in str(exc).lower()
        else:
            assert model._backend == "tabicl"
            assert s.evaluate("approve").metadata["backend"] == "tabicl"

    def test_tabicl_rejects_oversized_table(self, session_loader, monkeypatch):
        """The row-count guard fires before we ever touch the optional model."""
        from tabint.analysis.service.algorithms import supervised
        monkeypatch.setattr(supervised, "_TABICL_MAX_ROWS", 5)
        s = session_loader("loan_applications.csv")
        with pytest.raises(ValueError, match="up to ~5 rows"):
            s.train_classifier("is_approved", name="approve", backend="tabicl")


# --------------------------------------------------------------------------- #
# interpretation
# --------------------------------------------------------------------------- #

class TestInterpretation:
    def test_feature_importance_ranks_features(self, session_loader):
        s = session_loader("loan_applications.csv")
        model = s.train_classifier("is_approved", name="approve")
        r = s.feature_importance("approve")
        imp = r.values["importances"]
        assert set(imp) == set(model._feature_names)
        # sorted descending
        vals = list(imp.values())
        assert vals == sorted(vals, reverse=True)

    def test_explain_prediction_returns_contributions(self, session_loader):
        s = session_loader("loan_applications.csv")
        model = s.train_classifier("is_approved", name="approve")
        row = _first_row(s)
        r = s.explain_prediction("approve", row)
        assert set(r.values["contributions"]) == set(model._feature_names)
        assert "base_value" in r.values


# --------------------------------------------------------------------------- #
# dimensionality reduction
# --------------------------------------------------------------------------- #

class TestDimReduction:
    def test_pca_writes_components(self, session_loader):
        s = session_loader("customers.csv")
        r = s.reduce_dimensions("pca", n_components=2)
        assert r.values["columns"] == ["pca_0", "pca_1"]
        cols = _columns(s)
        assert "pca_0" in cols and "pca_1" in cols
        assert len(r.values["explained_variance_ratio"]) == 2

    def test_tsne_writes_components(self, session_loader):
        s = session_loader("customers.csv")
        r = s.reduce_dimensions("tsne", n_components=2)
        assert r.values["columns"] == ["tsne_0", "tsne_1"]

    def test_unknown_method_raises(self, session_loader):
        s = session_loader("customers.csv")
        with pytest.raises(ValueError):
            s.reduce_dimensions("nope")


# --------------------------------------------------------------------------- #
# time series
# --------------------------------------------------------------------------- #

class TestTimeSeries:
    def test_decompose_returns_components(self, session_loader):
        s = session_loader("monthly_sales.csv")
        r = s.decompose("month", "sales")
        assert {"trend", "seasonal", "residual"} <= set(r.values)
        assert len(r.values["trend"]) == 48

    def test_forecast_returns_horizon_points(self, session_loader):
        s = session_loader("monthly_sales.csv")
        r = s.forecast("month", "sales", horizon=6)
        assert len(r.values["forecast"]) == 6
        assert len(r.values["lower"]) == 6
        assert len(r.values["upper"]) == 6

    def test_detect_changepoints(self, session_loader):
        s = session_loader("monthly_sales.csv")
        r = s.detect_changepoints("month", "sales")
        assert r.method == "ruptures_pelt_rbf"
        assert isinstance(r.values["changepoints"], list)
        # segments partition the series; each carries a mean.
        assert r.values["segments"] and all("mean" in seg for seg in r.values["segments"])


# --------------------------------------------------------------------------- #
# insight primitives
# --------------------------------------------------------------------------- #

class TestKeyDrivers:
    def test_explain_metric_classification(self, session_loader):
        s = session_loader("customers.csv")
        r = s.explain_metric("is_churned")
        assert r.method == "decision_tree_key_drivers"
        assert r.values["drivers"]  # ranked feature->importance
        # sorted descending by importance
        vals = list(r.values["drivers"].values())
        assert vals == sorted(vals, reverse=True)
        assert isinstance(r.values["rules"], str)

    def test_explain_metric_regression(self, session_loader):
        s = session_loader("customers.csv")
        r = s.explain_metric("total_spend")
        assert r.metadata["task"] == "regression"
        assert "explained" in r.values

    def test_explain_metric_unknown_target_raises(self, session_loader):
        s = session_loader("customers.csv")
        with pytest.raises(ValueError):
            s.explain_metric("nope")


class TestMarketBasket:
    def test_market_basket_finds_rules(self, session_loader):
        s = session_loader("orders.csv")
        r = s.market_basket("customer_id", "product_id", min_support=0.05, min_confidence=0.1)
        assert r.method == "apriori_association_rules"
        assert isinstance(r.values["rules"], list)
        # every rule has the expected shape
        for rule in r.values["rules"]:
            assert {"antecedents", "consequents", "support", "confidence", "lift"} <= set(rule)


class TestCausal:
    def test_causal_effect_or_missing_dep(self, session_loader):
        s = session_loader("customers.csv")
        try:
            r = s.causal_effect("has_subscription", "total_spend")
        except ImportError as exc:
            assert "dowhy" in str(exc).lower()
        else:
            # Honesty seam: on a small/degenerate fixture the estimator declines
            # rather than emitting a meaningless effect.
            if r.trust and r.trust.declined:
                assert r.method == "causal_effect_declined"
                assert "effect" not in r.values
            else:
                assert r.method == "dowhy_backdoor_linear_regression"
                assert "effect" in r.values


class TestCohort:
    def test_rfm_segments_customers(self, session_loader):
        s = session_loader("transactions.csv")
        r = s.rfm("customer_id", "order_date", "amount")
        assert r.method == "rfm_quintile_segmentation"
        assert sum(r.values["segments"].values()) == r.metadata["n_customers"]

    def test_retention_cohorts_matrix(self, session_loader):
        s = session_loader("transactions.csv")
        r = s.retention_cohorts("customer_id", "order_date")
        assert r.method == "monthly_retention_cohorts"
        assert r.values["cohorts"]  # non-empty cohort → months map
        # month 0 retention is 1.0 for every cohort by construction
        for cohort, rates in r.values["retention_rates"].items():
            assert rates["0"] == 1.0 if "0" in rates else True


class TestComparePeriods:
    def test_compare_periods_reports_shift(self, session_loader):
        s = session_loader("monthly_sales.csv")
        r = s.compare_periods("month", "sales")
        assert r.method == "two_window_comparison"
        assert {"mean_before", "mean_after", "delta", "mannwhitney_p"} <= set(r.values)
