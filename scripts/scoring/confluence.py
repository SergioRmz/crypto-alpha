"""
Confluence math for crypto-alpha scoring engine v1.

Computes the 3 confidence components (trend_alignment,
volatility_suitability, structural_clarity) from a MarketContextSnapshot
and a reclassified regime. Returns a list of 3 component dicts ready
for the ConfidenceScore schema.

Per P2 D1: exactly 3 components in v1. Weights: 0.40 / 0.30 / 0.30.
Per P2 C5: null fields produce component-level data_sufficient=False
and a null_field_penalty (handled at the score.py level, not here).
"""
from __future__ import annotations

import numpy as np

from scripts.scoring.decimal_format import score_value
from scripts.scoring.strategy_version import COMPONENT_WEIGHTS


def _atr_pct_1h(snapshot: dict) -> float | None:
    tf = snapshot.get("timeframes", {}).get("1h")
    if not tf:
        return None
    val = tf.get("atr_pct")
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _bar_pct_change(tf: dict) -> float | None:
    if not tf:
        return None
    try:
        op = float(tf["open"])
        cl = float(tf["close"])
    except (KeyError, TypeError, ValueError):
        return None
    if op == 0:
        return None
    return (cl - op) / op * 100.0


def _data_sufficient(snapshot: dict) -> bool:
    """Trend alignment needs 1h and 4h bars with OHLC."""
    for tf_key in ("1h", "4h"):
        tf = snapshot.get("timeframes", {}).get(tf_key)
        if not tf:
            return False
        for field_key in ("open", "high", "low", "close"):
            if tf.get(field_key) is None:
                return False
    return True


def _data_sufficient_volatility(snapshot: dict) -> bool:
    """Volatility suitability needs realized_volatility_pct on 1d and atr_pct on 1h."""
    tf_1d = snapshot.get("timeframes", {}).get("1d")
    tf_1h = snapshot.get("timeframes", {}).get("1h")
    if not tf_1d or not tf_1h:
        return False
    if tf_1d.get("realized_volatility_pct") is None:
        return False
    if tf_1h.get("atr_pct") is None:
        return False
    return True


def _data_sufficient_structure(snapshot: dict) -> bool:
    """Structural clarity needs 1h and 4h bars; regime is provided."""
    return _data_sufficient(snapshot) and snapshot.get("regime") is not None


def trend_alignment(snapshot: dict) -> dict:
    """Multi-timeframe trend agreement, 0-1.

    Measures whether 1h and 4h bars agree on direction. 1.0 = strong
    agreement, 0.0 = strong disagreement.
    """
    tf_1h = snapshot.get("timeframes", {}).get("1h")
    tf_4h = snapshot.get("timeframes", {}).get("4h")
    sufficient = _data_sufficient(snapshot)

    if not sufficient:
        return {
            "name": "trend_alignment",
            "raw_value": 0.0,
            "max_value": 1.0,
            "weight": COMPONENT_WEIGHTS["trend_alignment"],
            "contribution": 0.0,
            "data_sufficient": False,
            "reasoning": "Insufficient data: missing 1h or 4h OHLC.",
        }

    h1_pct = _bar_pct_change(tf_1h)
    h4_pct = _bar_pct_change(tf_4h)
    if h1_pct is None or h4_pct is None:
        return {
            "name": "trend_alignment",
            "raw_value": 0.0,
            "max_value": 1.0,
            "weight": COMPONENT_WEIGHTS["trend_alignment"],
            "contribution": 0.0,
            "data_sufficient": False,
            "reasoning": "Insufficient data: could not compute 1h or 4h percent change.",
        }

    h1_dir = 1 if h1_pct > 0 else (-1 if h1_pct < 0 else 0)
    h4_dir = 1 if h4_pct > 0 else (-1 if h4_pct < 0 else 0)
    if h1_dir == h4_dir and h1_dir != 0:
        magnitudes = np.array([abs(h1_pct), abs(h4_pct)], dtype=np.float64)
        agreement = float(np.clip(np.min(magnitudes) / np.max(magnitudes), 0.0, 1.0))
        raw = 0.7 + 0.3 * agreement
    elif h1_dir == 0 or h4_dir == 0:
        raw = 0.3
    else:
        raw = 0.0

    contribution = score_value((raw / 1.0) * COMPONENT_WEIGHTS["trend_alignment"] * 100.0)
    return {
        "name": "trend_alignment",
        "raw_value": score_value(raw),
        "max_value": 1.0,
        "weight": COMPONENT_WEIGHTS["trend_alignment"],
        "contribution": contribution,
        "data_sufficient": True,
        "reasoning": f"1h pct={h1_pct:.3f}%, 4h pct={h4_pct:.3f}%, raw agreement={raw:.3f}.",
    }


def volatility_suitability(snapshot: dict) -> dict:
    """Whether the vol regime is compatible with the 1h holding horizon, 0-1.

    Sweet spot: realized_volatility_pct(1d) in [20, 60] and
    atr_pct(1h) in [0.10, 0.50]. Outside this range, the score
    degrades.
    """
    tf_1d = snapshot.get("timeframes", {}).get("1d")
    tf_1h = snapshot.get("timeframes", {}).get("1h")
    sufficient = _data_sufficient_volatility(snapshot)

    if not sufficient:
        return {
            "name": "volatility_suitability",
            "raw_value": 0.0,
            "max_value": 1.0,
            "weight": COMPONENT_WEIGHTS["volatility_suitability"],
            "contribution": 0.0,
            "data_sufficient": False,
            "reasoning": "Insufficient data: missing 1d realized_volatility_pct or 1h atr_pct.",
        }

    try:
        daily_vol = float(tf_1d["realized_volatility_pct"])
        hourly_atr = float(tf_1h["atr_pct"])
    except (KeyError, TypeError, ValueError):
        return {
            "name": "volatility_suitability",
            "raw_value": 0.0,
            "max_value": 1.0,
            "weight": COMPONENT_WEIGHTS["volatility_suitability"],
            "contribution": 0.0,
            "data_sufficient": False,
            "reasoning": "Insufficient data: bad types in volatility fields.",
        }

    daily_score = float(np.clip(1.0 - abs(daily_vol - 40.0) / 40.0, 0.0, 1.0))
    hourly_score = float(np.clip(1.0 - abs(hourly_atr - 0.30) / 0.30, 0.0, 1.0))
    raw = 0.5 * daily_score + 0.5 * hourly_score

    contribution = score_value((raw / 1.0) * COMPONENT_WEIGHTS["volatility_suitability"] * 100.0)
    return {
        "name": "volatility_suitability",
        "raw_value": score_value(raw),
        "max_value": 1.0,
        "weight": COMPONENT_WEIGHTS["volatility_suitability"],
        "contribution": contribution,
        "data_sufficient": True,
        "reasoning": (
            f"daily_vol={daily_vol:.1f}%, hourly_atr={hourly_atr:.2f}%, "
            f"raw suitability={raw:.3f}."
        ),
    }


def structural_clarity(snapshot: dict, regime: str) -> dict:
    """Whether the price action is tradeable, 0-1.

    In v1 this is a simple function of the (reclassified) regime.
    Veto regimes (chop, manipulation_probable, extreme_volatility,
    low_liquidity) yield 0.0. Trend regimes (trend_up, trend_down)
    yield 0.7-0.9. Range yields 0.4. Unknown yields 0.2.
    """
    sufficient = _data_sufficient_structure(snapshot)
    if not sufficient:
        return {
            "name": "structural_clarity",
            "raw_value": 0.0,
            "max_value": 1.0,
            "weight": COMPONENT_WEIGHTS["structural_clarity"],
            "contribution": 0.0,
            "data_sufficient": False,
            "reasoning": "Insufficient data: missing 1h/4h OHLC or regime.",
        }

    if regime in {"chop", "manipulation_probable", "extreme_volatility", "low_liquidity"}:
        raw = 0.0
    elif regime in {"trend_up", "trend_down"}:
        tf_1h = snapshot["timeframes"]["1h"]
        try:
            op = float(tf_1h["open"])
            cl = float(tf_1h["close"])
        except (KeyError, TypeError, ValueError):
            return {
                "name": "structural_clarity",
                "raw_value": 0.0,
                "max_value": 1.0,
                "weight": COMPONENT_WEIGHTS["structural_clarity"],
                "contribution": 0.0,
                "data_sufficient": False,
                "reasoning": "Insufficient data: bad 1h OHLC types.",
            }
        body = abs(cl - op) / op if op else 0
        raw = float(np.clip(0.7 + 0.2 * body * 100, 0.7, 0.9))
    elif regime == "range":
        raw = 0.4
    else:
        raw = 0.2

    contribution = score_value((raw / 1.0) * COMPONENT_WEIGHTS["structural_clarity"] * 100.0)
    return {
        "name": "structural_clarity",
        "raw_value": score_value(raw),
        "max_value": 1.0,
        "weight": COMPONENT_WEIGHTS["structural_clarity"],
        "contribution": contribution,
        "data_sufficient": True,
        "reasoning": f"regime={regime}, raw clarity={raw:.3f}.",
    }


def compute_components(snapshot: dict, regime: str) -> list[dict]:
    """Compute the 3 confidence components. Returns a list of 3 dicts."""
    return [
        trend_alignment(snapshot),
        volatility_suitability(snapshot),
        structural_clarity(snapshot, regime),
    ]


__all__ = [
    "compute_components",
    "trend_alignment",
    "volatility_suitability",
    "structural_clarity",
]
