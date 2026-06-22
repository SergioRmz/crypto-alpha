"""Tests for scripts.scoring.strategy_version."""
from __future__ import annotations

import hashlib
import json

import pytest

from scripts.scoring.strategy_version import (
    COMPONENT_WEIGHTS,
    CURRENT_VERSION,
    REGIME_VETO_REGIMES,
    TP_R_MULTIPLES,
    V0_1_0,
    StrategyVersion,
    build_v0_1_0,
)


def test_v0_1_0_is_frozen() -> None:
    assert V0_1_0.version_id == "v0.1.0"
    assert V0_1_0.fingerprint != ""


def test_v0_1_0_component_weights_sum_to_one() -> None:
    assert abs(sum(COMPONENT_WEIGHTS.values()) - 1.0) < 1e-9


def test_v0_1_0_veto_regimes() -> None:
    assert "chop" in REGIME_VETO_REGIMES
    assert "manipulation_probable" in REGIME_VETO_REGIMES
    assert "extreme_volatility" in REGIME_VETO_REGIMES
    assert "low_liquidity" in REGIME_VETO_REGIMES
    assert "trend_up" not in REGIME_VETO_REGIMES
    assert "range" not in REGIME_VETO_REGIMES


def test_v0_1_0_tp_r_multiples() -> None:
    assert TP_R_MULTIPLES == (1.0, 2.0, 3.0)


def test_v0_1_0_fingerprint_is_deterministic() -> None:
    a = build_v0_1_0()
    b = build_v0_1_0()
    assert a.fingerprint == b.fingerprint


def test_v0_1_0_fingerprint_matches_sha256_of_canonical_json() -> None:
    expected = hashlib.sha256(
        json.dumps(V0_1_0.rule_set_snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert V0_1_0.fingerprint == expected


def test_strategy_version_is_frozen_dataclass() -> None:
    with pytest.raises(Exception):
        V0_1_0.version_id = "v9.9.9"  # type: ignore[misc]


def test_current_version_constant_matches_v0_1_0() -> None:
    assert CURRENT_VERSION == V0_1_0.version_id


def test_strategy_version_to_dict_round_trip() -> None:
    d = V0_1_0.to_dict()
    assert d["version_id"] == "v0.1.0"
    assert d["fingerprint"] == V0_1_0.fingerprint
    assert d["component_weights"] == dict(COMPONENT_WEIGHTS)


def test_strategy_version_dataclass_construction() -> None:
    sv = StrategyVersion(
        version_id="v9.9.9",
        description="test",
        component_weights={"a": 1.0},
        rule_set_snapshot={"x": 1},
        fingerprint="abc",
    )
    assert sv.version_id == "v9.9.9"
