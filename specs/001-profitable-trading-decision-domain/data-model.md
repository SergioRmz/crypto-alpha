# Data Model: Profitable Trading Decision Domain

**Date**: 2026-06-17 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This document describes the conceptual entity graph for the crypto-alpha product domain. Concrete JSON Schemas will be drafted in P1; this file is the authoritative reference for field semantics and invariants.

## Entity graph

```text
TradingUniverse
    └── WatchlistAsset (many)         # dynamic, filtered by venue, liquidity, data availability

MarketContextSnapshot                # point-in-time market state for one or more assets
    ├── instrument
    ├── timeframe
    ├── regime                        # trend_up | trend_down | range | chop | manipulation_probable | extreme_volatility | low_liquidity
    ├── volatility
    ├── funding
    ├── open_interest
    └── captured_at (UTC)

Opportunity                          # potential trade idea, before becoming a Signal
    ├── instrument
    ├── direction                     # long | short
    ├── timeframe_context
    ├── thesis (human-readable)
    ├── detected_triggers[]           # liquidity_sweep, BOS, CHOCH, stopping_volume, order_block, FVG, ...
    ├── market_context_snapshot_ref
    ├── quality_status                # candidate | confirmed | rejected
    ├── rejection_reason              # when status == rejected
    └── evidence_refs[]               # pointers to captured snapshot slices

Signal                               # structured recommendation emitted by the system
    ├── opportunity_ref
    ├── direction
    ├── instrument
    ├── strategy_version_ref
    ├── triggers[]
    ├── confidence_score_ref
    ├── risk_plan_ref
    ├── alert_text (rendered; presentation layer)
    ├── issued_at (UTC)
    ├── disclaimer_present            # bool, MUST be true
    └── tracking_identity

RiskPlan
    ├── entry_zone_or_condition
    ├── stop_loss
    ├── take_profit_plan[]            # ordered list of TP levels
    ├── risk_reward_expectations[]     # R/R per TP
    ├── max_intended_holding_period
    └── invalidation_criteria

ConfidenceScore
    ├── components[]                  # { name, score, max_score, weight }
    ├── penalties[]                   # { name, deduction, reason }
    ├── total_score                   # 0..100, derived from components and penalties
    ├── bucket                        # 0-50 | 50-70 | 70-80 | 80-90 | 90-100
    └── strategy_version_ref

ManualTradeRecord                    # trader's actual execution
    ├── instrument
    ├── direction
    ├── entry_price, entry_timestamp
    ├── size_or_normalized_exposure
    ├── leverage (when used)
    ├── fees_paid                     # nullable
    ├── stop_loss (as actually placed)
    ├── take_profit_plan[] (as actually placed)
    ├── exit_price, exit_timestamp
    ├── signal_ref                    # optional; explicit when independent
    ├── execution_deviation_notes
    └── notes

TradeOutcome
    ├── signal_ref
    ├── manual_trade_ref              # optional
    ├── theoretical_signal_result     # what would have happened if signal had been followed exactly
    ├── actual_manual_result          # what really happened
    ├── realized_r_multiple
    ├── expected_value_in_r
    ├── max_favorable_excursion_r
    ├── max_adverse_excursion_r
    ├── time_in_trade_seconds
    ├── target_interaction            # hit_tp1 | hit_tp2 | hit_tp3 | hit_sl | hit_be | expired | invalidated
    ├── quality_labels[]              # thesis | timing | entry | stop | target | execution | regime
    └── outcome_resolved_at

LearningObservation
    ├── signal_ref
    ├── trade_outcome_ref
    ├── execution_deviation_ref
    ├── suggested_adjustments[]       # human-readable observations, not mutations
    ├── evidence_refs[]
    ├── strategy_version_ref
    └── created_at

StrategyVersion                      # immutable reference to a scoring/rule version
    ├── version_id
    ├── description
    ├── component_weights_snapshot
    ├── rule_set_snapshot
    └── created_at

ExecutionIntent                      # future-compatibility, read-only in v1
    ├── direction
    ├── instrument
    ├── entry_logic
    ├── stop_logic
    ├── target_logic
    ├── invalidation
    └── risk_constraints
```

## Invariants

These invariants MUST hold at every stage of the system. They are the contract between this spec and any later spec that builds on it.

1. **Provenance is unbroken.** Every `Signal` references an `Opportunity`, a `RiskPlan`, a `ConfidenceScore`, a `StrategyVersion`, and an evidence `MarketContextSnapshot`. (Spec SC-001)
2. **Manual trades are explicit about their relationship to signals.** A `ManualTradeRecord` either links to a `Signal`, is explicitly marked as a `modified_from_signal` deviation, or is marked as `independent`. (Spec SC-002)
3. **Theoretical and actual results are stored separately.** A `TradeOutcome` reports `theoretical_signal_result` and `actual_manual_result` independently. (Spec SC-003)
4. **No-trade is a real outcome.** An opportunity with `quality_status == rejected` has a `rejection_reason` and MUST NOT produce a `Signal`. (Spec SC-005)
5. **Quality labels are mandatory and plural where needed.** Every `TradeOutcome` carries at least one `quality_label`. (Spec SC-006)
6. **The v1 product does not place orders.** No entity in v1 wires `ExecutionIntent` to an order placement adapter. (Spec SC-007)
7. **Profitability reporting is R-anchored.** `realized_r_multiple` and `expected_value_in_r` are always present in any outcome record. (Spec SC-008, Q4)
8. **Versions are immutable.** A `StrategyVersion` is created once and never mutated; subsequent changes produce a new version.
9. **Disclaimers are mandatory on alerts.** `Signal.disclaimer_present == true` is a hard invariant. (Constitution I)
10. **Holding period is bounded.** `RiskPlan.max_intended_holding_period` is in the intraday-to-multi-day range per the constitution.

## Cardinality summary

| Relationship | Cardinality | Notes |
|---|---|---|
| `Opportunity` → `MarketContextSnapshot` | many → one | snapshot is shared across multiple opportunities |
| `Signal` → `Opportunity` | many → one | one signal per opportunity; one opportunity may produce zero signals (rejected) |
| `Signal` → `RiskPlan` | one → one | per signal |
| `Signal` → `ConfidenceScore` | one → one | per signal |
| `ManualTradeRecord` → `Signal` | many → zero-or-one | signal link is optional |
| `TradeOutcome` → `Signal` | many → one | one outcome per signal |
| `TradeOutcome` → `ManualTradeRecord` | one → zero-or-one | optional, when a manual trade was placed |
| `LearningObservation` → `TradeOutcome` | many → one | one outcome may produce many observations over time |
| `ConfidenceScore` → `StrategyVersion` | many → one | version reference is required |

## Lifecycle states

```text
Opportunity:
    candidate → confirmed → (promoted to Signal | rejected | expired)

Signal:
    pending → sent → active → (closed | invalidated | expired)
                                     └── (analyzed) → (learning observation generated)

ManualTradeRecord:
    planned → opened → (partial_closed | closed)
                              └── (outcome recorded)

TradeOutcome:
    open → resolved → (quality_labeled | calibration_observed)

LearningObservation:
    draft → reviewed → (accepted_into_learning_loop | rejected | parked)
```

These states are conceptual. A future spec will define the concrete enum values and the legal transitions; this spec defines the lifecycle vocabulary.

## Field conventions

- All timestamps are UTC, ISO 8601, with explicit `Z` suffix.
- All money-like fields use `Decimal`-compatible string representation in JSON; never `float`.
- All IDs are deterministic: `<entity_type>_<ulid>` for new records, `<entity_type>_<sha256(canonical_payload)>` for derived records.
- All enum values are lowercase snake_case.
- All human-readable fields (`thesis`, `notes`, `execution_deviation_notes`) are free text, may be empty, and MUST NOT contain advisory language (no "buy", "sell", "hold", "target price", "rating", "recommendation", "forecast").

## Deferred to later specs

- Concrete JSON Schemas (P1).
- Storage layout and migrations (a later spec, after P1).
- Confidence calibration formulas (P6).
- Regime classifier (P2).
- Alert rendering and channel adapters (P3).
- Position sizing math (P3).
- Multi-tenancy, billing, permissions (explicitly out of scope).
