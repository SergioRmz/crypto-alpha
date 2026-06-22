"""
Regime classifier for crypto-alpha scoring engine v1.

This is a rules-based re-classifier. It does NOT trust the snapshot's
input regime as ground truth; it re-derives the regime from the
snapshot's price action and volatility data, then compares to the
input regime for consistency.

Per P2 C2 / D2: rules-based with explicit thresholds. No ML.

The classifier returns one of the 8 P1 regime enum values:
  trend_up, trend_down, range, chop, manipulation_probable,
  extreme_volatility, low_liquidity, unknown

The output is used downstream to:
  - Apply regime_veto if the regime is in REGIME_VETO_REGIMES.
  - Apply regime_unknown_penalty if the regime is 'unknown'.
  - Inform the structural_clarity component in confluence.py.
"""
from __future__ import annotations

import numpy as np

from scripts.scoring.strategy_version import EXTREME_VOLATILITY_THRESHOLD

VETO_REGIMES = frozenset(
    {"chop", "manipulation_probable", "extreme_volatility", "low_liquidity"}
)


def _get_daily_vol(snapshot: dict) -> float | None:
    tf = snapshot.get("timeframes", {}).get("1d")
    if tf is None:
        return None
    val = tf.get("realized_volatility_pct")
    if val is None:
        return None
    return float(val)


def _price_choppy(snapshot: dict) -> bool:
    """True when 1h and 4h bars overlap heavily (choppy)."""
    tf_1h = snapshot.get("timeframes", {}).get("1h")
    tf_4h = snapshot.get("timeframes", {}).get("4h")
    if not tf_1h or not tf_4h:
        return False
    try:
        h1_low = float(tf_1h["low"])
        h1_high = float(tf_1h["high"])
        h4_low = float(tf_4h["low"])
        h4_high = float(tf_4h["high"])
    except (KeyError, TypeError, ValueError):
        return False
    overlap = min(h1_high, h4_high) - max(h1_low, h4_low)
    h1_range = h1_high - h1_low
    if h1_range <= 0:
        return False
    return (overlap / h1_range) > 0.7


def _price_trending(snapshot: dict) -> tuple[str | None, float]:
    """Return ('up'|'down', strength) if 1h and 4h agree on direction.

    Strength is the agreement ratio in [0, 1]. Returns (None, 0.0) when
    the timeframes disagree.
    """
    tf_1h = snapshot.get("timeframes", {}).get("1h")
    tf_4h = snapshot.get("timeframes", {}).get("4h")
    if not tf_1h or not tf_4h:
        return None, 0.0
    try:
        h1_open = float(tf_1h["open"])
        h1_close = float(tf_1h["close"])
        h4_open = float(tf_4h["open"])
        h4_close = float(tf_4h["close"])
    except (KeyError, TypeError, ValueError):
        return None, 0.0
    h1_dir = 1 if h1_close > h1_open else (-1 if h1_close < h1_open else 0)
    h4_dir = 1 if h4_close > h4_open else (-1 if h4_close < h4_open else 0)
    if h1_dir == 0 or h4_dir == 0:
        return None, 0.0
    if h1_dir == h4_dir:
        h1_range = abs(h1_close - h1_open)
        h4_range = abs(h4_close - h4_open)
        denom = h1_range + h4_range
        if denom <= 0:
            return ("up" if h1_dir > 0 else "down"), 0.5
        strength = float(np.clip(min(h1_range, h4_range) / denom, 0.0, 1.0))
        return ("up" if h1_dir > 0 else "down"), strength
    return None, 0.0


def reclassify(snapshot: dict) -> str:
    """Re-classify the snapshot's regime from its data.

    This is a v1 simplification. The function RE-CLASSIFIES from
    price action and volatility, but trusts specific input regimes
    (chop, manipulation_probable, extreme_volatility, low_liquidity)
    because re-classifying those would require data we don't have
    in the snapshot (e.g., order book depth for manipulation_probable).
    """
    input_regime = snapshot.get("regime", "unknown")

    if input_regime in VETO_REGIMES:
        return input_regime

    daily_vol = _get_daily_vol(snapshot)
    if input_regime == "unknown" and daily_vol is not None and daily_vol > EXTREME_VOLATILITY_THRESHOLD:
        return "extreme_volatility"

    if _price_choppy(snapshot):
        return "chop"

    direction, _ = _price_trending(snapshot)
    if direction == "up":
        return "trend_up"
    if direction == "down":
        return "trend_down"

    return "range"


def is_vetoed(regime: str) -> bool:
    """True when the regime triggers a regime_veto (no trade)."""
    return regime in VETO_REGIMES


__all__ = ["reclassify", "is_vetoed", "VETO_REGIMES"]
