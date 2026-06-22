"""
Scoring entrypoint and CLI for crypto-alpha scoring engine v1.

Public API:
    score_snapshot(snapshot: dict, snapshot_ref: str = "") -> ScoringOutput dict

CLI:
    python scripts/scoring/score.py score <snapshot.json> [output.json]
    python scripts/scoring/score.py validate <scored.json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from scripts.scoring import confluence, regime_classifier, risk_plan
from scripts.scoring.decimal_format import score_value
from scripts.scoring.strategy_version import (
    CURRENT_VERSION,
    NULL_FIELD_PENALTY_CAP,
    NULL_FIELD_PENALTY_PER_FIELD,
    REGIME_UNKNOWN_PENALTY,
    REGIME_VETO_PENALTY,
    SAFETY_VETO_PENALTY,
    TRADABLE_FLOOR,
)

REQUIRED_DERIV_FIELDS = (
    "funding_rate",
    "open_interest",
    "mark_price",
    "last_price",
)


def _bucket_for(total: float) -> str:
    if total < 50:
        return "no_trade"
    if total < 70:
        return "low"
    if total < 80:
        return "medium"
    if total < 90:
        return "high"
    return "exceptional"


def _null_field_penalties(snapshot: dict) -> list[dict]:
    """Produce one null_field_penalty per null field in derivatives_context."""
    penalties: list[dict] = []
    dc = snapshot.get("derivatives_context", {}) or {}
    for field_key in REQUIRED_DERIV_FIELDS:
        if dc.get(field_key) is None:
            penalties.append(
                {
                    "name": "null_field_penalty",
                    "deduction": NULL_FIELD_PENALTY_PER_FIELD,
                    "reason": f"field '{field_key}' is null in derivatives_context",
                    "field_path": f"derivatives_context.{field_key}",
                }
            )
    if penalties:
        total = sum(p["deduction"] for p in penalties)
        if total > NULL_FIELD_PENALTY_CAP:
            scale = NULL_FIELD_PENALTY_CAP / total
            for p in penalties:
                p["deduction"] = round(p["deduction"] * scale, 4)
    return penalties


def _build_confidence(
    components: list[dict],
    penalties: list[dict],
) -> dict:
    raw_total = sum(c["contribution"] for c in components) - sum(p["deduction"] for p in penalties)
    total = score_value(max(0.0, min(100.0, raw_total)))
    return {
        "schema_version": "0.1.0",
        "strategy_version_ref": CURRENT_VERSION,
        "components": components,
        "penalties": penalties,
        "total_score": total,
        "bucket": _bucket_for(total),
    }


def score_snapshot(snapshot: dict, snapshot_ref: str = "", scored_at: str | None = None) -> dict:
    """Run the scoring pipeline on a snapshot and return a ScoringOutput dict."""
    if scored_at is None:
        scored_at = "2026-06-21T12:00:00.000000Z"

    regime = regime_classifier.reclassify(snapshot)
    components = confluence.compute_components(snapshot, regime)
    penalties: list[dict] = []

    if regime_classifier.is_vetoed(regime):
        penalties.append(
            {
                "name": "regime_veto",
                "deduction": REGIME_VETO_PENALTY,
                "reason": f"regime '{regime}' is in the veto set; no trade",
            }
        )
    elif regime == "unknown":
        penalties.append(
            {
                "name": "regime_unknown_penalty",
                "deduction": REGIME_UNKNOWN_PENALTY,
                "reason": "regime is 'unknown'; classifier could not assign a stable regime",
            }
        )

    penalties.extend(_null_field_penalties(snapshot))

    confidence = _build_confidence(components, penalties)

    risk_plan_dict: dict | None = None
    rejection_reason: str | None = None

    if regime_classifier.is_vetoed(regime):
        rejection_reason = f"regime_veto: regime is '{regime}'"
    elif confidence["total_score"] < TRADABLE_FLOOR:
        rejection_reason = (
            f"tradable_floor: total_score {confidence['total_score']} < {TRADABLE_FLOOR}"
        )
    else:
        direction = risk_plan.recommend_direction(snapshot)
        rp, rej = risk_plan.derive_risk_plan(snapshot, direction)
        if rp is None:
            penalties.append(
                {
                    "name": "safety_veto",
                    "deduction": SAFETY_VETO_PENALTY,
                    "reason": rej or "risk plan derivation failed",
                }
            )
            confidence = _build_confidence(components, penalties)
            rejection_reason = f"safety_veto: {rej or 'risk plan derivation failed'}"
        elif direction == "neutral":
            rejection_reason = (
                "neutral_directional_lean: price is in the middle 50% of the 1h swing range"
            )
        else:
            risk_plan_dict = rp
            rejection_reason = None

    output: dict[str, Any] = {
        "schema_version": "0.1.0",
        "snapshot_ref": snapshot_ref or snapshot.get("canonical_symbol", "unknown"),
        "scored_at": scored_at,
        "confidence_score": confidence,
        "risk_plan": risk_plan_dict,
        "rejection_reason": rejection_reason,
    }
    return output


def _write_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(
            "Usage:\n"
            "  python scripts/scoring/score.py score <snapshot.json> [output.json]\n"
            "  python scripts/scoring/score.py validate <scored.json>\n",
            file=sys.stderr,
        )
        return 2

    subcommand = argv[0]
    if subcommand == "score":
        if len(argv) < 2:
            print("ERROR: 'score' requires a snapshot path", file=sys.stderr)
            return 2
        snapshot_path = Path(argv[1])
        snapshot = _read_json(snapshot_path)
        output = score_snapshot(snapshot, snapshot_ref=str(snapshot_path))
        if len(argv) >= 3:
            _write_json(output, Path(argv[2]))
            print(f"OK: wrote {argv[2]}", file=sys.stderr)
        else:
            print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    if subcommand == "validate":
        if len(argv) < 2:
            print("ERROR: 'validate' requires a scored JSON path", file=sys.stderr)
            return 2
        from scripts.validation.validate_scoring import validate_file

        return validate_file(Path(argv[1]))

    print(f"ERROR: unknown subcommand '{subcommand}'", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
