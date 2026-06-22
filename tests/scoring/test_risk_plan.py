"""Tests for scripts.scoring.risk_plan."""
from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from scripts.scoring.risk_plan import derive_risk_plan, recommend_direction


def _full_snap(
    entry: float = 100.0,
    swing_low: float = 95.0,
    swing_high: float = 105.0,
    atr_pct: float = 0.5,
    last_price: str = "100.0",
) -> dict:
    return {
        "timeframes": {
            "1h": {
                "open": str(entry),
                "high": str(swing_high),
                "low": str(swing_low),
                "close": str(entry),
                "atr_pct": str(atr_pct),
            }
        },
        "derivatives_context": {
            "last_price": last_price,
            "mark_price": last_price,
        },
    }


def test_recommend_direction_long() -> None:
    snap = _full_snap(entry=103.0, swing_low=95.0, swing_high=105.0)
    assert recommend_direction(snap) == "long"


def test_recommend_direction_short() -> None:
    snap = _full_snap(entry=97.0, swing_low=95.0, swing_high=105.0)
    assert recommend_direction(snap) == "short"


def test_recommend_direction_neutral() -> None:
    snap = _full_snap(entry=100.0, swing_low=95.0, swing_high=105.0)
    assert recommend_direction(snap) == "neutral"


def test_recommend_direction_missing_data() -> None:
    assert recommend_direction({"timeframes": {}}) == "neutral"


def test_derive_risk_plan_long() -> None:
    snap = _full_snap(entry=103.0, swing_low=95.0, swing_high=105.0, atr_pct=0.5)
    plan, rej = derive_risk_plan(snap, "long")
    assert plan is not None
    assert rej is None
    assert plan["direction"] == "long"
    assert float(plan["stop_loss"]) < float(plan["entry_zone"])
    assert len(plan["take_profit_plan"]) == 3
    for tp in plan["take_profit_plan"]:
        assert float(tp["price"]) > float(plan["entry_zone"])
        assert tp["r_multiple"] in (1.0, 2.0, 3.0)


def test_derive_risk_plan_short() -> None:
    snap = _full_snap(entry=97.0, swing_low=95.0, swing_high=105.0, atr_pct=0.5)
    plan, rej = derive_risk_plan(snap, "short")
    assert plan is not None
    assert rej is None
    assert plan["direction"] == "short"
    assert float(plan["stop_loss"]) > float(plan["entry_zone"])
    for tp in plan["take_profit_plan"]:
        assert float(tp["price"]) < float(plan["entry_zone"])


def test_derive_risk_plan_neutral_rejected() -> None:
    plan, rej = derive_risk_plan(_full_snap(), "neutral")
    assert plan is None
    assert "neutral" in (rej or "")


def test_derive_risk_plan_missing_atr_rejected() -> None:
    snap = {"timeframes": {"1h": {"open": "100", "high": "105", "low": "95", "close": "103"}}, "derivatives_context": {"last_price": "100"}}
    plan, rej = derive_risk_plan(snap, "long")
    assert plan is None
    assert rej is not None


def test_derive_risk_plan_missing_1h_rejected() -> None:
    plan, rej = derive_risk_plan({"timeframes": {}, "derivatives_context": {"last_price": "100"}}, "long")
    assert plan is None


def test_derive_risk_plan_no_reference_price_rejected() -> None:
    snap = {
        "timeframes": {"1h": {"open": "100", "high": "105", "low": "95", "close": "103", "atr_pct": "0.5"}},
        "derivatives_context": {"last_price": None, "mark_price": None},
    }
    plan, rej = derive_risk_plan(snap, "long")
    assert plan is None
    assert "reference price" in (rej or "")


def test_derive_risk_plan_tp1_at_1r() -> None:
    snap = _full_snap(entry=103.0, swing_low=95.0, swing_high=105.0, atr_pct=0.5)
    plan, _ = derive_risk_plan(snap, "long")
    assert plan is not None
    entry = float(plan["entry_zone"])
    stop = float(plan["stop_loss"])
    tp1 = float(plan["take_profit_plan"][0]["price"])
    r_distance = entry - stop
    assert abs((tp1 - entry) - r_distance) < 1e-6


def test_derive_risk_plan_tp3_at_3r() -> None:
    snap = _full_snap(entry=103.0, swing_low=95.0, swing_high=105.0, atr_pct=0.5)
    plan, _ = derive_risk_plan(snap, "long")
    assert plan is not None
    entry = float(plan["entry_zone"])
    stop = float(plan["stop_loss"])
    tp3 = float(plan["take_profit_plan"][2]["price"])
    r_distance = entry - stop
    assert abs((tp3 - entry) - 3.0 * r_distance) < 1e-6


def test_derive_risk_plan_short_tp1_at_1r() -> None:
    snap = _full_snap(entry=97.0, swing_low=95.0, swing_high=105.0, atr_pct=0.5)
    plan, _ = derive_risk_plan(snap, "short")
    assert plan is not None
    entry = float(plan["entry_zone"])
    stop = float(plan["stop_loss"])
    tp1 = float(plan["take_profit_plan"][0]["price"])
    r_distance = stop - entry
    assert abs((entry - tp1) - r_distance) < 1e-6


def test_derive_risk_plan_max_holding_period_is_valid() -> None:
    snap = _full_snap(entry=103.0, swing_low=95.0, swing_high=105.0)
    plan, _ = derive_risk_plan(snap, "long")
    assert plan is not None
    assert plan["max_intended_holding_period"] in {"1m", "5m", "15m", "1h", "4h", "1d"}


def test_derive_risk_plan_invalidation_criteria_nonempty() -> None:
    snap = _full_snap(entry=103.0, swing_low=95.0, swing_high=105.0)
    plan, _ = derive_risk_plan(snap, "long")
    assert plan is not None
    assert len(plan["invalidation_criteria"]) >= 1


def test_derive_risk_plan_risk_reward_expectations_mirror_tps() -> None:
    snap = _full_snap(entry=103.0, swing_low=95.0, swing_high=105.0)
    plan, _ = derive_risk_plan(snap, "long")
    assert plan is not None
    tp_levels = [tp["level"] for tp in plan["take_profit_plan"]]
    rr_levels = [rr["level"] for rr in plan["risk_reward_expectations"]]
    assert tp_levels == rr_levels


@given(
    entry=st.floats(min_value=50.0, max_value=50000.0, allow_nan=False, allow_infinity=False),
    swing_low=st.floats(min_value=50.0, max_value=50000.0, allow_nan=False, allow_infinity=False),
    swing_high=st.floats(min_value=50.0, max_value=50000.0, allow_nan=False, allow_infinity=False),
    atr_pct=st.floats(min_value=0.01, max_value=5.0, allow_nan=False, allow_infinity=False),
)
def test_derive_risk_plan_long_always_has_correct_stop_side(
    entry: float, swing_low: float, swing_high: float, atr_pct: float
) -> None:
    if swing_high <= swing_low:
        return
    if not (swing_low <= entry <= swing_high):
        return
    snap = _full_snap(entry=entry, swing_low=swing_low, swing_high=swing_high, atr_pct=atr_pct)
    snap["timeframes"]["1h"]["close"] = str(swing_high + 1.0)
    plan, rej = derive_risk_plan(snap, "long")
    if plan is None:
        assert rej is not None
        return
    assert float(plan["stop_loss"]) < float(plan["entry_zone"])


@given(
    entry=st.floats(min_value=50.0, max_value=50000.0, allow_nan=False, allow_infinity=False),
    swing_low=st.floats(min_value=50.0, max_value=50000.0, allow_nan=False, allow_infinity=False),
    swing_high=st.floats(min_value=50.0, max_value=50000.0, allow_nan=False, allow_infinity=False),
    atr_pct=st.floats(min_value=0.01, max_value=5.0, allow_nan=False, allow_infinity=False),
)
def test_derive_risk_plan_short_always_has_correct_stop_side(
    entry: float, swing_low: float, swing_high: float, atr_pct: float
) -> None:
    if swing_high <= swing_low:
        return
    if not (swing_low <= entry <= swing_high):
        return
    snap = _full_snap(entry=entry, swing_low=swing_low, swing_high=swing_high, atr_pct=atr_pct)
    snap["timeframes"]["1h"]["close"] = str(swing_low - 1.0)
    plan, rej = derive_risk_plan(snap, "short")
    if plan is None:
        assert rej is not None
        return
    assert float(plan["stop_loss"]) > float(plan["entry_zone"])
