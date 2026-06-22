"""
Strategy Version registry for crypto-alpha scoring engine v1.

This module defines StrategyVersion v0.1.0 — the only scoring rules
version in P2. The rules table is frozen at module load time.

Per P0 Invariant 8: StrategyVersion is created once and never mutated.
Subsequent changes produce a new version (e.g., v0.2.0).

The fingerprint is the SHA-256 of the canonical JSON serialization
of the rules table, which makes the version's identity mechanical:
the same rules always produce the same fingerprint.

Per P0 FR-018: every ConfidenceScore and RiskPlan references a
StrategyVersion. In P2, that reference is always "v0.1.0".
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

CURRENT_VERSION = "v0.1.0"
DOMINANT_TIMEFRAME = "1h"
TRADABLE_FLOOR = 50.0
ATR_STOP_MULTIPLIER = 1.5
REGIME_VETO_REGIMES = frozenset(
    {"chop", "manipulation_probable", "extreme_volatility", "low_liquidity"}
)
NULL_FIELD_PENALTY_PER_FIELD = 10.0
NULL_FIELD_PENALTY_CAP = 30.0
REGIME_UNKNOWN_PENALTY = 15.0
REGIME_VETO_PENALTY = 100.0
SAFETY_VETO_PENALTY = 100.0
EXTREME_VOLATILITY_THRESHOLD = 100.0
COMPONENT_WEIGHTS: dict[str, float] = {
    "trend_alignment": 0.40,
    "volatility_suitability": 0.30,
    "structural_clarity": 0.30,
}
TP_R_MULTIPLES: tuple[float, ...] = (1.0, 2.0, 3.0)
DEFAULT_HOLDING_PERIOD = "1h"


@dataclass(frozen=True)
class StrategyVersion:
    """Immutable reference to a scoring rules version."""

    version_id: str
    description: str
    component_weights: dict[str, float] = field(default_factory=dict)
    rule_set_snapshot: dict[str, Any] = field(default_factory=dict)
    fingerprint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id": self.version_id,
            "description": self.description,
            "component_weights": dict(self.component_weights),
            "rule_set_snapshot": self.rule_set_snapshot,
            "fingerprint": self.fingerprint,
        }


def _canonical_json(obj: dict[str, Any]) -> str:
    """Serialize obj with sorted keys and no extra whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def build_v0_1_0() -> StrategyVersion:
    """Build the frozen v0.1.0 rules table and compute its fingerprint."""
    rule_set: dict[str, Any] = {
        "version_id": CURRENT_VERSION,
        "dominant_timeframe": DOMINANT_TIMEFRAME,
        "tradable_floor": TRADABLE_FLOOR,
        "atr_stop_multiplier": ATR_STOP_MULTIPLIER,
        "regime_veto_regimes": sorted(REGIME_VETO_REGIMES),
        "null_field_penalty_per_field": NULL_FIELD_PENALTY_PER_FIELD,
        "null_field_penalty_cap": NULL_FIELD_PENALTY_CAP,
        "regime_unknown_penalty": REGIME_UNKNOWN_PENALTY,
        "regime_veto_penalty": REGIME_VETO_PENALTY,
        "safety_veto_penalty": SAFETY_VETO_PENALTY,
        "extreme_volatility_threshold": EXTREME_VOLATILITY_THRESHOLD,
        "tp_r_multiples": list(TP_R_MULTIPLES),
        "default_holding_period": DEFAULT_HOLDING_PERIOD,
        "component_weights": dict(COMPONENT_WEIGHTS),
    }
    canonical = _canonical_json(rule_set)
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return StrategyVersion(
        version_id=CURRENT_VERSION,
        description="Initial scoring rules. Rules-based, deterministic, auditable.",
        component_weights=dict(COMPONENT_WEIGHTS),
        rule_set_snapshot=rule_set,
        fingerprint=fingerprint,
    )


V0_1_0: StrategyVersion = build_v0_1_0()

__all__ = [
    "StrategyVersion",
    "V0_1_0",
    "CURRENT_VERSION",
    "DOMINANT_TIMEFRAME",
    "TRADABLE_FLOOR",
    "ATR_STOP_MULTIPLIER",
    "REGIME_VETO_REGIMES",
    "NULL_FIELD_PENALTY_PER_FIELD",
    "NULL_FIELD_PENALTY_CAP",
    "REGIME_UNKNOWN_PENALTY",
    "REGIME_VETO_PENALTY",
    "SAFETY_VETO_PENALTY",
    "EXTREME_VOLATILITY_THRESHOLD",
    "TP_R_MULTIPLES",
    "DEFAULT_HOLDING_PERIOD",
    "COMPONENT_WEIGHTS",
]
