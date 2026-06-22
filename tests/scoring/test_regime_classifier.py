"""Tests for scripts.scoring.regime_classifier."""
from __future__ import annotations

from hypothesis import given, strategies as st

from scripts.scoring.regime_classifier import is_vetoed, reclassify


def _snap(regime: str, h1: dict | None = None, h4: dict | None = None, d1: dict | None = None) -> dict:
    tfs: dict = {}
    if h1 is not None:
        tfs["1h"] = h1
    if h4 is not None:
        tfs["4h"] = h4
    if d1 is not None:
        tfs["1d"] = d1
    return {"regime": regime, "timeframes": tfs}


def test_reclassify_trusts_veto_regimes() -> None:
    for veto in ("chop", "manipulation_probable", "extreme_volatility", "low_liquidity"):
        snap = _snap(veto, h1={"open": "100", "high": "101", "low": "99", "close": "100.5"})
        assert reclassify(snap) == veto


def test_reclassify_extreme_volatility_from_daily_vol() -> None:
    snap = _snap(
        "unknown",
        h1={"open": "100", "high": "101", "low": "99", "close": "100.5"},
        h4={"open": "100", "high": "101", "low": "99", "close": "100.5"},
        d1={"realized_volatility_pct": "150.0"},
    )
    assert reclassify(snap) == "extreme_volatility"


def test_reclassify_choppy_when_timeframes_overlap_heavily() -> None:
    snap = _snap(
        "unknown",
        h1={"open": "100", "high": "101", "low": "99", "close": "100.0"},
        h4={"open": "99.5", "high": "100.5", "low": "99.0", "close": "100.2"},
        d1={"realized_volatility_pct": "40.0"},
    )
    assert reclassify(snap) == "chop"


def test_reclassify_trend_up_when_both_bars_up() -> None:
    snap = _snap(
        "unknown",
        h1={"open": "100", "high": "102", "low": "99", "close": "101"},
        h4={"open": "98", "high": "103", "low": "97", "close": "101.5"},
        d1={"realized_volatility_pct": "40.0"},
    )
    assert reclassify(snap) == "trend_up"


def test_reclassify_trend_down_when_both_bars_down() -> None:
    snap = _snap(
        "unknown",
        h1={"open": "101", "high": "102", "low": "99", "close": "100"},
        h4={"open": "103", "high": "103.5", "low": "100", "close": "100.5"},
        d1={"realized_volatility_pct": "40.0"},
    )
    assert reclassify(snap) == "trend_down"


def test_reclassify_range_when_neutral() -> None:
    snap = _snap(
        "unknown",
        h1={"open": "100", "high": "101", "low": "99", "close": "100.0"},
        h4={"open": "100", "high": "102", "low": "98", "close": "99.5"},
        d1={"realized_volatility_pct": "40.0"},
    )
    assert reclassify(snap) in ("range", "chop")


def test_reclassify_handles_missing_data() -> None:
    assert reclassify({"regime": "unknown", "timeframes": {}}) == "range"
    assert reclassify({"regime": "trend_up", "timeframes": {}}) == "trend_up"


def test_is_vetoed() -> None:
    assert is_vetoed("chop") is True
    assert is_vetoed("manipulation_probable") is True
    assert is_vetoed("extreme_volatility") is True
    assert is_vetoed("low_liquidity") is True
    assert is_vetoed("trend_up") is False
    assert is_vetoed("range") is False
    assert is_vetoed("unknown") is False


@given(st.sampled_from(["chop", "manipulation_probable", "extreme_volatility", "low_liquidity", "unknown"]))
def test_reclassify_returns_known_regime(regime: str) -> None:
    snap = _snap(regime)
    result = reclassify(snap)
    assert result in {
        "trend_up",
        "trend_down",
        "range",
        "chop",
        "manipulation_probable",
        "extreme_volatility",
        "low_liquidity",
        "unknown",
    }


@given(
    h1_open=st.floats(min_value=50, max_value=50000, allow_nan=False, allow_infinity=False),
    h1_close=st.floats(min_value=50, max_value=50000, allow_nan=False, allow_infinity=False),
)
def test_reclassify_never_crashes_on_valid_bars(h1_open: float, h1_close: float) -> None:
    lo = min(h1_open, h1_close) - 1
    hi = max(h1_open, h1_close) + 1
    snap = _snap(
        "unknown",
        h1={"open": str(h1_open), "high": str(hi), "low": str(lo), "close": str(h1_close)},
        h4={"open": str(h1_open), "high": str(hi), "low": str(lo), "close": str(h1_close)},
        d1={"realized_volatility_pct": "40.0"},
    )
    out = reclassify(snap)
    assert out in {
        "trend_up",
        "trend_down",
        "range",
        "chop",
        "manipulation_probable",
        "extreme_volatility",
        "low_liquidity",
        "unknown",
    }
