# Research: Profitable Trading Decision Domain

**Date**: 2026-06-17 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This document captures the domain research and design precedents that informed the spec. It is not a market survey; it is a record of why the entity model looks the way it does.

## Why this domain shape

### Trading intelligence ≠ signal bot

Most "crypto signal" products treat each alert as an isolated event. That design choice makes post-hoc learning almost impossible: you cannot tell whether a loss was caused by a bad thesis, a bad entry, or a bad stop, because the alert does not carry the evidence needed to distinguish them.

alpha-signal separates **opportunity** (what the market offered), **signal** (what the system recommended), **manual trade** (what the trader actually did), and **outcome** (what the market did) so each can be evaluated and the gaps between them can be measured.

### Opportunities must be comparable across assets

The user requirement is explicit: dynamic multi-asset watchlist, not BTC-only. That forces the opportunity model to be **instrument-agnostic** at the decision layer. Concrete fields like `entry_price` and `stop_loss` are present, but the comparison logic uses normalized fields: `risk_per_unit`, `size_or_normalized_exposure`, `realized_r_multiple`, `expected_value_in_r`, `regime`, `confidence_components[]`. This is why the spec has 12 entities instead of a single `Trade` record.

### Manual execution deviation is signal, not noise

When the trader deviates from a system signal — entering later, sizing differently, exiting early — that deviation is data. If the system does not record it, the backtest looks better than reality, and learning drifts. The `ManualTradeRecord` and the `theoretical_signal_result` vs `actual_manual_result` split in `TradeOutcome` are designed to keep the two views of performance from contaminating each other.

### Confidence must be decomposable

A monolithic confidence number (e.g. "92%") is opaque and unauditable. The spec forces `ConfidenceScore` to be a structure with components, penalties, and a `strategy_version` reference. This is the only way to do meaningful calibration later: when outcomes disagree with confidence, the system must be able to show which component was wrong.

### No-trade is a valid outcome

A common failure mode in signal products is forcing the model to "always have an opinion". The spec explicitly elevates `rejected` to a first-class state for opportunities and ties it to a `rejection_reason`. This is required by the constitution's "selectivity over volume" principle and by the quality gates introduced in clarification Q1.

## Why these entities and not others

| Candidate entity | Decision | Rationale |
|---|---|---|
| `Trade` (single entity) | **Rejected** | Cannot represent signal vs manual deviation, cannot represent rejected opportunities, cannot decompose confidence. |
| `Alert` as the top-level concept | **Rejected** | Alerts are presentation-layer. The system's recommendation is a `Signal`; the alert is just one channel. |
| `Strategy` as a top-level entity | **Rejected for now** | Strategy is a `version` of scoring rules, not a top-level aggregate. Versioned, not first-class. |
| `Regime` as a top-level entity | **Rejected for now** | A regime is a value, not an entity. Captured as a field on `MarketContextSnapshot` and on the trade records. |
| `ExecutionIntent` | **Kept (read-only)** | Required for future-compatibility with supervised/automated execution. Not wired to anything in this spec. |
| `LearningObservation` | **Kept (read-only)** | Required for traceability. Does not mutate strategy behavior in this spec. |

## Precedent scan (informational, non-binding)

- **Spec-Driven Development with Spec Kit** is the project's chosen governance model and is reflected in `.specify/`.
- **Constitution-first design** (a la Amazon-style "working backwards" or project constitutions in OSS) provides the principles every later spec must satisfy.
- **Event-sourced trading journals** in the OSS trading space typically follow the opportunity/signal/trade/outcome split (sometimes called "thesis → decision → execution → outcome"). alpha-signal follows that lineage and makes the version reference explicit.
- **Versioned strategy weights** are a known requirement for any system that wants to detect when a recent change is responsible for a recent improvement. Without versioned weights, every backtest is contaminated by unrecorded rule changes.

## Open research questions (deferred to later specs)

- Concrete JSON Schemas for each entity. Drafted in conceptual form in this spec; finalized in P1 and later.
- Confidence calibration algorithm (isotonic regression vs Platt scaling vs Brier score). Deferred to P6.
- Regime taxonomy and classifier implementation. Deferred to P2.
- Alert message template and channel adapters (Telegram, file, webhook). Deferred to P3.
- Position sizing and risk-per-trade formulas. Deferred to P3 alongside `RiskPlan` derivation.

## Conclusion

The spec is internally consistent, constitution-compliant, and ready to anchor the next spec (P1, data layer). No blocking research items remain in P0.
