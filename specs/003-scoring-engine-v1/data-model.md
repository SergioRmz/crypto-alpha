# Data Model: Scoring Engine v1

**Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

This document describes the field-level precision for the three JSON Schemas produced by P2: `ConfidenceScore`, `RiskPlan`, and `ScoringOutput`. The JSON Schema files in `contracts/` are the authoritative machine-readable form; this document is the human-readable companion for design decisions and edge cases.

## Entity: `ConfidenceScore`

A decomposable confidence assessment with exactly 3 components in v1, a penalty array, a `total_score` in 0-100, a `bucket`, and a `strategy_version_ref`.

### Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | yes | Semver of the schema this score conforms to. P2 value: `"0.1.0"`. |
| `strategy_version_ref` | string | yes | Reference to the `StrategyVersion` that produced this score. P2 value: `"v0.1.0"`. |
| `components` | array of `Component` | yes | Exactly 3 entries in v1. See "Components" below. |
| `penalties` | array of `Penalty` | yes | May be empty. See "Penalties" below. |
| `total_score` | number | yes | `clamp(sum(component.contribution) - sum(penalty.deduction), 0, 100)`. Rounded to 4 decimal places. |
| `bucket` | string (enum) | yes | Derived from `total_score`. One of: `"no_trade"` (0-50), `"low"` (50-70), `"medium"` (70-80), `"high"` (80-90), `"exceptional"` (90-100). |

### Components

Each `Component` is a named, weighted contributor to the score.

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string (enum) | yes | One of: `"trend_alignment"`, `"volatility_suitability"`, `"structural_clarity"`. |
| `raw_value` | number | yes | The raw measurement underlying this component (e.g., trend strength 0-1, vol ratio, structure score 0-1). Range: 0-1 in v1. |
| `max_value` | number | yes | The maximum value `raw_value` can take. Always `1` in v1. |
| `weight` | number | yes | The weight applied to this component's contribution. In v1: `0.40` for trend_alignment, `0.30` for volatility_suitability, `0.30` for structural_clarity. Weights sum to 1.00. |
| `contribution` | number | yes | `round((raw_value / max_value) * weight * 100, 4)`. The score this component contributes to the total. |
| `data_sufficient` | boolean | yes | `false` when the snapshot's input data for this component is partial (e.g., a null field required for the calculation). `true` when the component was computed with full data. |
| `reasoning` | string | no | Human-readable explanation of how the component was computed. For audit purposes. |

### Penalties

Each `Penalty` is a named deduction from the score.

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string (enum) | yes | One of: `"null_field_penalty"`, `"regime_veto"`, `"regime_unknown_penalty"`, `"safety_veto"`. |
| `deduction` | number | yes | The amount to subtract from the total. Range: 0-100. |
| `reason` | string | yes | Human-readable explanation of the penalty. |
| `field_path` | string | no | For `null_field_penalty`, the JSON pointer of the affected field. |

### Penalty rules in v1

| Name | Deduction | Trigger |
|---|---|---|
| `regime_veto` | 100 (capped at total) | Snapshot regime is `chop`, `manipulation_probable`, `extreme_volatility`, or `low_liquidity`. Forces `total_score = 0` and `risk_plan = null`. |
| `regime_unknown_penalty` | 15 | Snapshot regime is `unknown` and no regime veto triggered. |
| `null_field_penalty` | 10 per field (capped at 30 total across all `null_field_penalty` entries) | A field in `derivatives_context` is `null`. |
| `safety_veto` | 100 (capped at total) | The recommended side's stop would be on the wrong side of entry (ATR floor violation). Forces `total_score = 0` and `risk_plan = null`. |

### Invariants

1. Exactly 3 components, with names from the strict enum.
2. Component weights sum to 1.00 (±1e-9).
3. `total_score` is in `[0, 100]` and matches the formula within ±1e-6.
4. `bucket` is derived, not stored; it is the result of `bucket_for(total_score)`.
5. `regime_veto` and `safety_veto` are mutually exclusive (only one can apply, but both can be absent).
6. Sum of `null_field_penalty` deductions ≤ 30.

## Entity: `RiskPlan`

The derived trade management structure. Emitted only when the scoring run is not vetoed and the directional lean is not `neutral`.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | yes | Semver. P2 value: `"0.1.0"`. |
| `strategy_version_ref` | string | yes | Reference to the `StrategyVersion`. P2 value: `"v0.1.0"`. |
| `direction` | string (enum) | yes | One of: `"long"`, `"short"`. |
| `entry_zone` | string | yes | Decimal string. The proposed entry price. |
| `stop_loss` | string | yes | Decimal string. The stop-loss price. |
| `take_profit_plan` | array of `TPLevel` | yes | Exactly 3 entries in v1. |
| `risk_reward_expectations` | array of `RRExpectation` | yes | Exactly 3 entries in v1, mirroring `take_profit_plan`. |
| `max_intended_holding_period` | string (enum) | yes | One of: `"1m"`, `"5m"`, `"15m"`, `"1h"`, `"4h"`, `"1d"`. P2 default: `"1h"`. |
| `invalidation_criteria` | array of string | yes | Non-empty list. E.g., `"close < stop_loss"`, `"regime change to chop"`, `"4h close breaks swing low"`. |
| `notes` | string \| null | no | Free text. MUST NOT contain advisory language (Constitution I). |

### `TPLevel`

| Field | Type | Required | Description |
|---|---|---|---|
| `level` | integer | yes | 1, 2, or 3 (P2 has exactly 3 TPs). |
| `price` | string | yes | Decimal string. The TP price. |
| `r_multiple` | number | yes | The R multiple at this TP. Exactly 1.0, 2.0, 3.0 in v1. |

### `RRExpectation`

| Field | Type | Required | Description |
|---|---|---|---|
| `level` | integer | yes | 1, 2, or 3. Mirrors the TP level. |
| `r_multiple` | number | yes | The expected R multiple if this TP is hit. Exactly 1.0, 2.0, 3.0 in v1. |
| `hit_probability_pct` | number | no | Optional estimate of the probability this TP is hit. P2 does not compute this; it is left for a future spec. |

### Invariants

1. For `direction: long`, `stop_loss < entry_zone` and `take_profit_plan[i].price > entry_zone` for all i.
2. For `direction: short`, `stop_loss > entry_zone` and `take_profit_plan[i].price < entry_zone` for all i.
3. `|entry_zone - stop_loss| >= 1.5 × ATR` of the dominant timeframe (1h in v1).
4. `take_profit_plan` has exactly 3 entries with R-multiples 1.0, 2.0, 3.0.
5. `risk_reward_expectations` has exactly 3 entries, one per TP.
6. `max_intended_holding_period` is in the P0 intraday-to-multi-day range.
7. `invalidation_criteria` is non-empty.
8. `notes` (when present) does not contain advisory language.

## Entity: `ScoringOutput`

A wrapper that ties a `snapshot_ref` to a `confidence_score` and an optional `risk_plan`.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | yes | Semver. P2 value: `"0.1.0"`. |
| `snapshot_ref` | string | yes | Path or identifier of the input `MarketContextSnapshot` (e.g., `"specs/002-data-layer/fixtures/btc-perp-snapshot.json"`). |
| `scored_at` | string | yes | ISO 8601 UTC with `Z` suffix. When the scoring run happened. **Note**: For P2 fixture reproducibility, the `scored_at` is the run-time timestamp; it does NOT appear in the byte-equality check (P2 fixtures use a fixed timestamp embedded in the fixture file). |
| `confidence_score` | `ConfidenceScore` | yes | The decomposable score. Always present, even when `risk_plan` is null. |
| `risk_plan` | `RiskPlan` \| null | yes | The derived risk plan. `null` when the run is a no-trade (veto, neutral lean, score below tradable floor). |
| `rejection_reason` | string \| null | yes (when risk_plan is null) | Human-readable explanation of why the run did not produce a risk plan. `null` when `risk_plan` is non-null. |
| `notes` | string \| null | no | Free text. Optional. |

### Invariants

1. When `risk_plan` is `null`, `rejection_reason` MUST be a non-empty string naming the veto or threshold.
2. When `risk_plan` is non-null, `rejection_reason` MUST be `null`.
3. `confidence_score` is always present and is a valid `ConfidenceScore` (per its schema).
4. `scored_at` is ISO 8601 UTC with `Z` suffix.

## Field conventions (P2, inherited from P0 and P1)

- All timestamps are UTC ISO 8601 with explicit `Z` suffix.
- All money-like fields use decimal-string representation (8 decimal places for prices, 4 decimal places for scores, 1 decimal place for R-multiples).
- All enum values are lowercase snake_case.
- All IDs (when introduced) are deterministic: `<entity_type>_<ulid>` for new records.
- All human-readable fields (`reasoning`, `reason`, `notes`, `invalidation_criteria`) are free text, may be empty or null, and MUST NOT contain advisory language (Constitution I).

## Cardinality summary

| Relationship | Cardinality | Notes |
|---|---|---|
| `ScoringOutput` → `MarketContextSnapshot` | one → one | One scoring run per snapshot. |
| `ScoringOutput` → `ConfidenceScore` | one → one | Always present. |
| `ScoringOutput` → `RiskPlan` | one → zero-or-one | Optional. `null` for no-trade runs. |
| `ConfidenceScore` → `Component` | one → 3 (fixed) | Exactly 3 in v1. |
| `RiskPlan` → `TPLevel` | one → 3 (fixed) | Exactly 3 in v1. |
| `ConfidenceScore` → `StrategyVersion` | one → one | Always `v0.1.0` in P2. |

## Deferred to later specs

- Funding carry scoring (R1).
- Liquidity suitability formula (R2).
- Breakout detection (R3).
- ML-based scoring (R4).
- Cross-asset confluence (R5).
- Multi-strategy / portfolio scoring (R6).
- Weight calibration from outcomes (R7, P6).
- ATR multiplier tuning (R8, P6).
- TP probability estimation (currently `hit_probability_pct` is optional and not computed in P2).
- Dynamic `max_intended_holding_period` based on volatility regime (currently fixed at `1h`).
- Regime classifier override (currently P2 re-classifies; a future spec may allow the input `regime` to short-circuit the classifier).
