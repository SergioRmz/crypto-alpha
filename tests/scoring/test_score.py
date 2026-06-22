"""Tests for scripts.scoring.score (the public API)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.scoring.score import score_snapshot

P1_FIXTURES = Path("specs/002-data-layer/fixtures")


def _load(name: str) -> dict:
    return json.loads((P1_FIXTURES / name).read_text())


def test_score_btc_long() -> None:
    snap = _load("btc-perp-snapshot.json")
    out = score_snapshot(snap, "specs/002-data-layer/fixtures/btc-perp-snapshot.json")
    assert out["schema_version"] == "0.1.0"
    cs = out["confidence_score"]
    assert len(cs["components"]) == 3
    assert 0.0 <= cs["total_score"] <= 100.0
    assert cs["bucket"] in {"no_trade", "low", "medium", "high", "exceptional"}
    if out["risk_plan"] is not None:
        assert out["rejection_reason"] is None
        assert out["risk_plan"]["strategy_version_ref"] == "v0.1.0"
        assert len(out["risk_plan"]["take_profit_plan"]) == 3
    else:
        assert out["rejection_reason"] is not None


def test_score_eth_neutral_or_directional() -> None:
    snap = _load("eth-perp-snapshot.json")
    out = score_snapshot(snap, "eth")
    assert out["confidence_score"]["total_score"] >= 0.0


def test_score_sol_vetoed_by_extreme_volatility() -> None:
    snap = _load("sol-perp-snapshot.json")
    out = score_snapshot(snap, "sol")
    assert out["risk_plan"] is None
    assert out["rejection_reason"] is not None
    assert "extreme_volatility" in out["rejection_reason"] or "tradable_floor" in out["rejection_reason"]


def test_score_determinism() -> None:
    snap = _load("btc-perp-snapshot.json")
    a = score_snapshot(snap, "btc", scored_at="2026-06-21T12:00:00.000000Z")
    b = score_snapshot(snap, "btc", scored_at="2026-06-21T12:00:00.000000Z")
    assert a == b


def test_score_chop_veto() -> None:
    snap = {
        "regime": "chop",
        "timeframes": {
            "1h": {"open": "100", "high": "101", "low": "99", "close": "100", "atr_pct": "0.3"},
            "4h": {"open": "100", "high": "101", "low": "99", "close": "100"},
            "1d": {"realized_volatility_pct": "40.0"},
        },
        "derivatives_context": {"last_price": "100", "mark_price": "100", "funding_rate": "0", "open_interest": "1"},
    }
    out = score_snapshot(snap, "chop-test")
    assert out["risk_plan"] is None
    assert any(p["name"] == "regime_veto" for p in out["confidence_score"]["penalties"])


def test_score_unknown_regime_gets_unknown_penalty() -> None:
    snap = {
        "regime": "unknown",
        "timeframes": {
            "1h": {"open": "100", "high": "105", "low": "99", "close": "104", "atr_pct": "0.3"},
            "4h": {"open": "100", "high": "106", "low": "98", "close": "105"},
            "1d": {"realized_volatility_pct": "40.0"},
        },
        "derivatives_context": {"last_price": "104", "mark_price": "104", "funding_rate": "0", "open_interest": "1"},
    }
    out = score_snapshot(snap, "unknown-test")
    penalties = [p["name"] for p in out["confidence_score"]["penalties"]]
    assert "regime_unknown_penalty" in penalties


def test_score_null_derivatives_produce_penalties() -> None:
    snap = {
        "regime": "trend_up",
        "timeframes": {
            "1h": {"open": "100", "high": "105", "low": "99", "close": "104", "atr_pct": "0.3"},
            "4h": {"open": "100", "high": "106", "low": "98", "close": "105"},
            "1d": {"realized_volatility_pct": "40.0"},
        },
        "derivatives_context": {"last_price": None, "mark_price": None, "funding_rate": None, "open_interest": None},
    }
    out = score_snapshot(snap, "null-test")
    penalties = out["confidence_score"]["penalties"]
    null_penalties = [p for p in penalties if p["name"] == "null_field_penalty"]
    assert len(null_penalties) >= 3


def test_score_tradable_floor_enforced() -> None:
    snap = {
        "regime": "range",
        "timeframes": {
            "1h": {"open": "100", "high": "101", "low": "99", "close": "100.5", "atr_pct": "0.05"},
            "4h": {"open": "100", "high": "101", "low": "99", "close": "100.0"},
            "1d": {"realized_volatility_pct": "20.0"},
        },
        "derivatives_context": {"last_price": "100.5", "mark_price": "100.5", "funding_rate": "0", "open_interest": "1"},
    }
    out = score_snapshot(snap, "floor-test")
    if out["confidence_score"]["total_score"] < 50:
        assert out["risk_plan"] is None
        assert "tradable_floor" in (out["rejection_reason"] or "")


def test_score_handles_missing_timeframes_gracefully() -> None:
    snap = {"regime": "unknown", "timeframes": {}, "derivatives_context": {}}
    out = score_snapshot(snap, "empty")
    assert out["confidence_score"]["total_score"] == 0.0
    assert out["risk_plan"] is None


@pytest.mark.parametrize(
    "fixture_name",
    ["btc-perp-snapshot.json", "eth-perp-snapshot.json", "sol-perp-snapshot.json"],
)
def test_score_all_p1_fixtures(fixture_name: str) -> None:
    snap = _load(fixture_name)
    out = score_snapshot(snap, fixture_name)
    assert "schema_version" in out
    assert "confidence_score" in out
    assert "risk_plan" in out
    assert "rejection_reason" in out
    assert 0.0 <= out["confidence_score"]["total_score"] <= 100.0
