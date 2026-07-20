"""Tests for validation.assumptions — the checks that route test selection."""
import numpy as np

from tabint.validation import assumptions


def test_is_normal_true_for_gaussian():
    rng = np.random.default_rng(0)
    assert assumptions.is_normal(rng.normal(0, 1, 500)) is True


def test_is_normal_false_for_skewed():
    rng = np.random.default_rng(0)
    assert assumptions.is_normal(rng.exponential(1.0, 500)) is False


def test_is_normal_false_for_constant():
    assert assumptions.is_normal([5, 5, 5, 5, 5]) is False


def test_is_normal_false_for_too_few():
    assert assumptions.is_normal([1.0, 2.0]) is False


def test_has_equal_variance_true():
    rng = np.random.default_rng(1)
    a = rng.normal(0, 1, 200)
    b = rng.normal(0, 1, 200)
    assert assumptions.has_equal_variance(a, b) is True


def test_has_equal_variance_false():
    rng = np.random.default_rng(1)
    a = rng.normal(0, 1, 200)
    b = rng.normal(0, 10, 200)
    assert assumptions.has_equal_variance(a, b) is False


def test_enough_samples():
    assert assumptions.enough_samples(range(20), range(25)) is True
    assert assumptions.enough_samples(range(20), range(5)) is False


def test_expected_counts_ok():
    big = [[50, 40], [45, 55]]
    tiny = [[1, 2], [1, 1]]
    assert assumptions.expected_counts_ok(big) is True
    assert assumptions.expected_counts_ok(tiny) is False
