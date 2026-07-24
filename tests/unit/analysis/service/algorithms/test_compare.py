"""Unit tests for the compare_periods algorithm — via the FakeStore.

compare_periods only calls ``store.get_frame()``, so the DuckDB/Workspace layer
is fully faked. Exercises the honesty seam's small-sample behaviour.

Mirrors: src/tabint/analysis/service/algorithms/compare.py
"""
import numpy as np
import pandas as pd

from tabint.shared.honesty import TrustLevel


def test_compare_periods_attaches_low_trust_on_small_sample(fake_store):
    from tabint.analysis.service.algorithms.compare import compare_periods

    df = pd.DataFrame(
        {
            "t": pd.date_range("2024-01-01", periods=20, freq="D"),
            "v": np.arange(20, dtype=float),
        }
    )
    res = compare_periods(fake_store(df), "t", "v")
    assert res.trust is not None
    assert res.trust.level == TrustLevel.LOW           # 10 per window < 30
    assert res.trust.declined is False
    assert any("before/after" in c.lower() for c in res.trust.caveats)
