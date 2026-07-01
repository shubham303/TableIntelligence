"""Tests for operation identity and caching key computation."""
import pandas as pd
import pytest

from tabular.identity import fingerprint_dataframe, fingerprint_series, operation_key


def test_operation_key_is_deterministic():
    """Same inputs always produce the same key."""
    key1 = operation_key("cluster", {"n_clusters": 3}, "abc123")
    key2 = operation_key("cluster", {"n_clusters": 3}, "abc123")
    assert key1 == key2


def test_operation_key_is_hex_string():
    """Key is a 64-character hex string (SHA-256)."""
    key = operation_key("profile", {}, "abc123")
    assert len(key) == 64
    assert all(c in "0123456789abcdef" for c in key)


def test_operation_key_differs_by_name():
    key1 = operation_key("cluster", {"n": 3}, "fp")
    key2 = operation_key("profile", {"n": 3}, "fp")
    assert key1 != key2


def test_operation_key_differs_by_params():
    key1 = operation_key("cluster", {"n_clusters": 3}, "fp")
    key2 = operation_key("cluster", {"n_clusters": 5}, "fp")
    assert key1 != key2


def test_operation_key_differs_by_fingerprint():
    key1 = operation_key("cluster", {}, "fp_a")
    key2 = operation_key("cluster", {}, "fp_b")
    assert key1 != key2


def test_operation_key_params_order_independent():
    """Dict param ordering must not affect the key."""
    key1 = operation_key("train", {"target": "y", "n": 3}, "fp")
    key2 = operation_key("train", {"n": 3, "target": "y"}, "fp")
    assert key1 == key2


def test_fingerprint_series_is_deterministic():
    s = pd.Series([1, 2, 3, 4, 5])
    assert fingerprint_series(s) == fingerprint_series(s)


def test_fingerprint_series_differs_on_different_data():
    s1 = pd.Series([1, 2, 3])
    s2 = pd.Series([1, 2, 4])
    assert fingerprint_series(s1) != fingerprint_series(s2)


def test_fingerprint_series_is_order_sensitive():
    """[1, 2, 3] and [3, 2, 1] must have different fingerprints."""
    s1 = pd.Series([1, 2, 3])
    s2 = pd.Series([3, 2, 1])
    assert fingerprint_series(s1) != fingerprint_series(s2)


def test_fingerprint_dataframe_is_deterministic():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert fingerprint_dataframe(df) == fingerprint_dataframe(df)


def test_fingerprint_dataframe_differs_on_different_data():
    df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df2 = pd.DataFrame({"a": [1, 2], "b": [3, 5]})
    assert fingerprint_dataframe(df1) != fingerprint_dataframe(df2)
