"""
Risk plan derivation for crypto-alpha scoring engine v1.

Derives a RiskPlan from a MarketContextSnapshot, the recommended
direction (long/short/neutral), and a reclassified regime.

Per P2 C3: entry_zone is swing-based on the dominant timeframe (1h).
  long if close > swing_low + 0.5 * range
  short if close < swing_high - 0.5 * range
  else neutral

Per P2 C4: stop_loss is hybrid ATR + swing.
  stop = entry ± max(1.5 * ATR, |entry - swing_extreme|)
  The wider of the two is chosen.

Per P2 C17: 3 TP levels at 1R, 2R, 3R.

Per P2 C16: returns None (and a rejection_reason) when:
  - regime is vetoed (caller's responsibility; this module assumes
    the regime has already been vetted)
  - the recommended side's stop would invert (ATR floor violation)
  - the direction is 'neutral'

The function returns a dict with shape:
  {"risk_plan": <plan dict> | None, "rejection_reason": <str> | None}
"""
from __future__ import annotations

import numpy as np

# Make the package importable when running as a script.
import sys
from pathlib import Path
_PKG_PARENT = Path(__file__).resolve().parents[2]
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

from scripts.scoring.decimal_format import price as fmt_price  # noqa: E402
from scripts.scoring.decimal_format import r_multiple  # noqa: E402
from scripts.scoring.strategy_version import (  # noqa: E402
    ATR_STOP_MULTIPLIER,
    DEFAULT_HOLDING_PERIOD,
    TP_R_MULTIPLES,
)


def _atr_pct_to_price(atr_pct: float, reference_price: float) -> float:
    """Convert an atr_pct (e.g. 0.18 means 0.18%) to a price distance."""
    return abs(reference_price) * (atr_pct / 100.0)


def _get_swing(snapshot: dict, tf_key: str) -> tuple[float, float, float] | None:
    """Return (swing_low, swing_high, close) for the given timeframe, or None."""
    tf = snapshot.get("timeframes", {}).get(tf_key)
    if not tf:
        return None
    try:
        lo = float(tf["low"])
        hi = float(tf["high"])
        cl = float(tf["close"])
    except (KeyError, TypeError, ValueError):
        return None
    return lo, hi, cl


def recommend_direction(snapshot: dict, tf_key: str = "1h") -> str:
    """Return 'long', 'short', or 'neutral' based on the swing zone."""
    swing = _get_swing(snapshot, tf_key)
    if swing is None:
        return "neutral"
    lo, hi, cl = swing
    rng = hi - lo
    if rng <= 0:
        return "neutral"
    midpoint_lo = lo + 0.5 * rng
    midpoint_hi = hi - 0.5 * rng
    if cl > midpoint_hi:
        return "long"
    if cl < midpoint_lo:
        return "short"
    return "neutral"


def _atr_pct_for(snapshot: dict, tf_key: str) -> float | None:
    tf = snapshot.get("timeframes", {}).get(tf_key)
    if not tf:
        return None
    val = tf.get("atr_pct")
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _reference_price(snapshot: dict) -> float | None:
    """Prefer last_price, then mark_price, then 1h close."""
    dc = snapshot.get("derivatives_context", {})
    for key in ("last_price", "mark_price"):
        val = dc.get(key)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                pass
    swing = _get_swing(snapshot, "1h")
    if swing is not None:
        return swing[2]
    return None


def derive_risk_plan(snapshot: dict, direction: str) -> tuple[dict | None, str | None]:
    """Derive a RiskPlan dict (and rejection_reason) for the given direction.

    Returns (risk_plan, None) on success or (None, rejection_reason) on failure.
    """
    if direction not in {"long", "short"}:
        return None, f"directional lean is '{direction}', not long/short"

    swing = _get_swing(snapshot, DEFAULT_HOLDING_PERIOD)
    if swing is None:
        return None, "missing 1h swing data (OHLC)"
    swing_low, swing_high, close = swing

    atr_pct = _atr_pct_for(snapshot, DEFAULT_HOLDING_PERIOD)
    if atr_pct is None:
        return None, f"missing {DEFAULT_HOLDING_PERIOD} atr_pct"

    ref_price = _reference_price(snapshot)
    if ref_price is None or ref_price <= 0:
        return None, "no usable reference price (last/mark/1h close all null)"

    if direction == "long":
        entry = close
        swing_extreme = swing_low
        atr_distance = _atr_pct_to_price(atr_pct, ref_price)
        swing_distance = abs(entry - swing_extreme)
        candidate_distance = max(ATR_STOP_MULTIPLIER * atr_distance, swing_distance)
        stop = entry - candidate_distance
        if stop >= entry:
            return None, "safety_veto: ATR floor would invert stop for long"
        if stop <= 0:
            return None, "safety_veto: stop would be non-positive"
        r_distance = entry - stop
        tps = [
            {"level": 1, "price": fmt_price(entry + 1.0 * r_distance), "r_multiple": r_multiple(1.0)},
            {"level": 2, "price": fmt_price(entry + 2.0 * r_distance), "r_multiple": r_multiple(2.0)},
            {"level": 3, "price": fmt_price(entry + 3.0 * r_distance), "r_multiple": r_multiple(3.0)},
        ]
        invalidation = [
            f"close < stop_loss ({fmt_price(stop)})",
            "regime change to chop or manipulation_probable",
            f"1h close breaks swing low ({fmt_price(swing_low)})",
        ]
    else:
        entry = close
        swing_extreme = swing_high
        atr_distance = _atr_pct_to_price(atr_pct, ref_price)
        swing_distance = abs(swing_extreme - entry)
        candidate_distance = max(ATR_STOP_MULTIPLIER * atr_distance, swing_distance)
        stop = entry + candidate_distance
        if stop <= entry:
            return None, "safety_veto: ATR floor would invert stop for short"
        r_distance = stop - entry
        tps = [
            {"level": 1, "price": fmt_price(entry - 1.0 * r_distance), "r_multiple": r_multiple(1.0)},
            {"level": 2, "price": fmt_price(entry - 2.0 * r_distance), "r_multiple": r_multiple(2.0)},
            {"level": 3, "price": fmt_price(entry - 3.0 * r_distance), "r_multiple": r_multiple(3.0)},
        ]
        invalidation = [
            f"close > stop_loss ({fmt_price(stop)})",
            "regime change to chop or manipulation_probable",
            f"1h close breaks swing high ({fmt_price(swing_high)})",
        ]

    risk_plan = {
        "schema_version": "0.1.0",
        "strategy_version_ref": "v0.1.0",
        "direction": direction,
        "entry_zone": fmt_price(entry),
        "stop_loss": fmt_price(stop),
        "take_profit_plan": tps,
        "risk_reward_expectations": [
            {"level": t["level"], "r_multiple": t["r_multiple"]} for t in tps
        ],
        "max_intended_holding_period": DEFAULT_HOLDING_PERIOD,
        "invalidation_criteria": invalidation,
        "notes": (
            "TP1 typically used for partial exit; TP2 and TP3 are runner targets. "
            "Adjust position sizing per account risk rules; this plan is structural, not sized."
        ),
    }
    return risk_plan, None


__all__ = ["recommend_direction", "derive_risk_plan"]
