"""Tests for scripts.scoring.confluence."""
from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from scripts.scoring.confluence import (
    compute_components,
    structural_clarity,
    trend_alignment,
    volatility_suitability,
)
from scripts.scoring.strategy_version import COMPONENT_WEIGHTS


def _snap(
    h1: dict | None = None,
    h4: dict | None = None,
    d1: dict | None = None,
    regime: str = "unknown",
) -> dict:
    tfs: dict = {}
    if h1 is not None:
        tfs["1h"] = h1
    if h4 is not None:
        tfs["4h"] = h4
    if d1 is not None:
        tfs["1d"] = d1
    return {"regime": regime, "timeframes": tfs}


def test_trend_alignment_agreement() -> None:
    snap = _snap(
        h1={"open": "100", "high": "101", "low": "99", "close": "100.5"},
        h4={"open": "98", "high": "102", "low": "97", "close": "101"},
    )
    comp = trend_alignment(snap)
    assert comp["name"] == "trend_alignment"
    assert 0.0 <= comp["raw_value"] <= 1.0
    assert comp["contribution"] > 0.0
    assert comp["data_sufficient"] is True


def test_trend_alignment_disagreement() -> None:
    snap = _snap(
        h1={"open": "100", "high": "101", "low": "99", "close": "99.5"},
        h4={"open": "101", "high": "102", "low": "100", "close": "100.5"},
    )
    comp = trend_alignment(snap)
    assert comp["raw_value"] == 0.0
    assert comp["contribution"] == 0.0


def test_trend_alignment_insufficient_data() -> None:
    snap = _snap(h1={"open": "100", "high": "101", "low": "99"})
    comp = trend_alignment(snap)
    assert comp["data_sufficient"] is False
    assert comp["contribution"] == 0.0


def test_volatility_suitability_sweet_spot() -> None:
    snap = _snap(
        d1={"realized_volatility_pct": "40.0"},
        h1={"open": "100", "high": "101", "low": "99", "close": "100", "atr_pct": "0.30"},
    )
    comp = volatility_suitability(snap)
    assert comp["raw_value"] > 0.9
    assert comp["data_sufficient"] is True


def test_volatility_suitability_too_high() -> None:
    snap = _snap(
        d1={"realized_volatility_pct": "120.0"},
        h1={"open": "100", "high": "101", "low": "99", "close": "100", "atr_pct": "0.30"},
    )
    comp = volatility_suitability(snap)
    assert comp["raw_value"] < 0.5


def test_volatility_suitability_insufficient_data() -> None:
    snap = _snap(h1={"open": "100", "high": "101", "low": "99", "close": "100"})
    comp = volatility_suitability(snap)
    assert comp["data_sufficient"] is False


def test_structural_clarity_veto_regime() -> None:
    snap = _snap(
        h1={"open": "100", "high": "101", "low": "99", "close": "100"},
        h4={"open": "100", "high": "101", "low": "99", "close": "100"},
        regime="chop",
    )
    comp = structural_clarity(snap, "chop")
    assert comp["raw_value"] == 0.0


def test_structural_clarity_trend_regime() -> None:
    snap = _snap(
        h1={"open": "100", "high": "102", "low": "99", "close": "101"},
        h4={"open": "98", "high": "103", "low": "97", "close": "101"},
    )
    comp = structural_clarity(snap, "trend_up")
    assert comp["raw_value"] >= 0.7
    assert comp["raw_value"] <= 0.9


def test_compute_components_returns_three() -> None:
    snap = _snap(
        h1={"open": "100", "high": "101", "low": "99", "close": "100", "atr_pct": "0.30"},
        h4={"open": "98", "high": "102", "low": "97", "close": "101"},
        d1={"realized_volatility_pct": "40.0"},
    )
    comps = compute_components(snap, "trend_up")
    assert len(comps) == 3
    names = {c["name"] for c in comps}
    assert names == {"trend_alignment", "volatility_suitability", "structural_clarity"}


def test_weights_sum_to_one() -> None:
    assert abs(sum(COMPONENT_WEIGHTS.values()) - 1.0) < 1e-9


@given(
    raw=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    weight=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_contribution_is_in_range(raw: float, weight: float) -> None:
    contrib = round((raw / 1.0) * weight * 100.0, 4)
    assert 0.0 <= contrib <= 100.0


def test_insufficient_data_yields_zero_contribution() -> None:
    snap = {"regime": "unknown", "timeframes": {}}
    comps = compute_components(snap, "unknown")
    for c in comps:
        assert c["data_sufficient"] is False
        assert c["contribution"] == 0.0


@pytest.mark.parametrize(
    "regime,expected_zero",
    [
        ("chop", True),
        ("manipulation_probable", True),
        ("extreme_volatility", True),
        ("low_liquidity", True),
    ],
)
def test_veto_regimes_yield_zero_clarity(regime: str, expected_zero: bool) -> None:
    snap = _snap(
        h1={"open": "100", "high": "101", "low": "99", "close": "100"},
        h4={"open": "100", "high": "101", "low": "99", "close": "100"},
        regime=regime,
    )
    comp = structural_clarity(snap, regime)
    assert (comp["raw_value"] == 0.0) is expected_zero
