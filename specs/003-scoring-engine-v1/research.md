# Research: Scoring Engine v1 Design Decisions

**Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This document captures the design precedents, the "why this shape" reasoning for every P2 design decision, and the open research questions deferred to later specs. It is the Phase 0 output of the planning workflow.

## Why a rules-based scoring engine?

P0 defined `ConfidenceScore` and `RiskPlan` as entities. P1 anchored the data shape with `MarketContextSnapshot`. P2's job is to **close the loop from raw data to a structured, auditable interpretation of "is this tradeable right now, and if so, how?"**

The choice between rules-based, ML-based, and hybrid scoring has been a defining decision in quantitative trading for 40 years. For P2, the constraints from P0 narrow the choice:

1. **Constitution IV (Traceable Decisions)** requires every score to be explainable from stored evidence. ML models with millions of parameters fail this test by default.
2. **Constitution VI (Learning Requires Evidence, Versioning, and Guardrails)** prohibits silent mutation. ML training that adjusts weights in response to new data without versioning is precisely the "silent mutation" the constitution bans.
3. **P0 FR-012** explicitly requires confidence to be "decomposable" rather than an opaque number. A rules-based scorer is naturally decomposable; an ML scorer requires post-hoc explanation (SHAP, LIME) that adds complexity without satisfying the spirit of the requirement.

So P2 is rules-based. ML-based scoring is a future spec, gated by a calibration spec (P6) and a dedicated review. The pattern is **rules now, learn from outcomes later (P5-P6), maybe ML much later (P9+)**.

## Precedent scan

### A. Trading rules as auditable tables

The "rules table" pattern is universal in classical technical analysis. The canonical references (Edwards & Magee, John Murphy, Pring) all express setups as named conditions on price/volume/volatility data. A "score" in this tradition is a sum of weighted indicators. P2's `ConfidenceScore` is a digital version of this: 3 named conditions, each with a weight, summed and penalized.

**Where we differ**: classical technical analysis uses visual inspection; P2 uses mechanical computation. The names of the components (`trend_alignment`, `volatility_suitability`, `structural_clarity`) are intentionally human-readable so the next-phase developer (and you, two months from now) can read a score and understand what the system "saw".

### B. Nautilus Trader's `Strategy` and `Indicator` model

Nautilus Trader (https://nautilustrader.io) is a Rust/Python hybrid trading platform. Its `Strategy` class wraps a set of `Indicator` instances. Each indicator emits a value; the strategy combines them via a `SignalGenerator`. Indicators are pure functions on bars; signals are the strategy's interpretation.

**Where we differ**: Nautilus strategies are typically stateful (they react to new bars as they arrive). P2's scorer is **stateless** — it consumes a single snapshot and emits a single scoring output. P3 (signal generator) will be the stateful component. P2 is the pure-function core.

### C. Backtrader's `Analyzer` and `Observer` model

Backtrader (https://www.backtrader.com) separates "strategy" (when to trade) from "analyzer" (what to measure). Analyzers compute things like Sharpe ratio, drawdown, SQN. The structure is similar to P2's: a strategy emits signals, an analyzer evaluates them.

**Where we differ**: Backtrader is backtest-oriented; P2 is forward-looking. The scorer's job is to estimate quality *before* a trade, not to measure it after. P5 (outcome capture) is P2's "analyzer" counterpart.

### D. TA-Lib and the indicator ecosystem

TA-Lib (https://ta-lib.org) is a C library of ~200 technical indicators (RSI, MACD, Bollinger, ATR, ADX, etc.). It's the de-facto standard for indicator computation in Python trading systems. P2 uses NumPy for math but borrows the indicator-naming convention: each component has a name, a raw value, a max value, and a weight.

**Where we differ**: TA-Lib's indicators are mostly visual tools for charts; P2's components are decision-driving. A `trend_alignment` component in P2 is *defined* in the strategy rules table, not pulled from TA-Lib. (Future P2+ specs may add TA-Lib as a dependency for advanced indicators, but P2 ships with hand-rolled components.)

## Design decisions and rationale

### D1. Three confidence components, not five or seven

**Decision**: Exactly 3 components in v1: `trend_alignment`, `volatility_suitability`, `structural_clarity`.

**Rationale**: Three is the smallest set that covers the three orthogonal dimensions of trade quality:
- **Trend alignment** (do the timeframes agree on direction?)
- **Volatility suitability** (is the vol regime compatible with the holding horizon?)
- **Structural clarity** (is the price action tradeable, or choppy?)

Adding `funding_carry` (C in your B1 menu) would require a meaningful `funding_rate` signal; the P1 fixtures all have `funding_rate: 0.0001` to `0.0003`, which is too small to drive a component. Adding `liquidity_context` would require reliable depth data; P1's `liquidity_suitability` is `null` by design (P1's FR-014, owned by P2 — but P2 defers computing it because the data is not in the snapshot).

Both can be added in P6+ once the inputs become reliable. P2 keeps the surface small and the math tractable.

**Trade-off**: A 3-component score is less expressive than a 5- or 7-component score. The benefit is that every component matters — a regression in any one of the three is visible immediately. With 7 components, noise can hide signal.

### D2. Rules-based regime classifier with explicit thresholds

**Decision**: The regime classifier is a small table of rules. Each rule is a one-liner with a unit test. No ML, no learned weights.

**Rationale** (full reasoning at top of this doc): Constitution IV (traceable) + Constitution VI (versioned) + P0 FR-012 (decomposable) ⇒ rules-based.

The rules table for v1 is:

| Condition | New regime | Notes |
|---|---|---|
| `regime: chop` (input) | `chop` | trust input |
| `regime: manipulation_probable` (input) | `manipulation_probable` | trust input |
| `regime: extreme_volatility` (input) | `extreme_volatility` | trust input |
| `regime: low_liquidity` (input) | `low_liquidity` | trust input |
| `regime: trend_up/trend_down/range` (input) AND 4h close aligns | input regime | re-verify the input |
| `regime: unknown` (input) AND `realized_volatility_pct(1d) > 100` | `extreme_volatility` | high-vol fallback |
| `regime: unknown` (input) AND price action is choppy (1h and 4h ranges overlap) | `chop` | choppy fallback |
| `regime: unknown` (input) AND price action is trending (1h and 4h agree) | `trend_up` or `trend_down` | trending fallback |
| `regime: unknown` (input) AND none of the above | `range` | neutral fallback |
| anything else | `unknown` (preserved) | last resort |

The classifier does NOT call the existing P1 snapshot's `regime` field as ground truth; it RE-CLASSIFIES from price action and volatility. The snapshot's `regime` is used only to detect veto and unknown states. This is a v1 simplification documented in spec assumptions.

**Trade-off**: The classifier may disagree with a human's manual regime label on edge cases. P5 (outcome capture) will produce `quality_labels[]` that include `regime`; if a "this was trend_up" outcome keeps getting labeled as "regime-mismatch", that's signal to tune the classifier.

### D3. Swing-based entry zone

**Decision**: `entry_zone` is derived from the most recent swing high/low on the dominant timeframe (1h in v1). The score recommends `long` if `close > swing_low + 0.5 × range` and `short` if `close < swing_high - 0.5 × range`.

**Rationale**: Swing-based entry is the most common pattern in classical technical analysis. It is mechanical (no judgment), auditable (one rule, one test), and produces concrete price levels (which the `RiskPlan` schema requires).

The 0.5 × range midpoint is the "neutral" zone: if `close` is in the middle 50% of the swing range, the directional lean is `neutral` and no `RiskPlan` is emitted. This avoids forcing a directional call when the price is in a no-man's-land.

**Trade-off**: Swing-based entry misses breakouts (where price leaves a range). P3 (signal generator) can add breakout detection on top of P2's output. P2 keeps it simple.

### D4. Hybrid ATR+swing stop loss

**Decision**: `stop_loss = entry ± max(1.5 × ATR, |entry - swing_extreme|)`. The more conservative of the two is chosen. The direction follows `RiskPlan.direction`.

**Rationale**: P0 Q1 says "stop-loss level is identifiable in market structure, not arbitrary". A pure ATR stop is mechanical but ignores market structure (it can sit right in the middle of a swing). A pure swing stop respects structure but is brittle in low-volatility environments (a tiny swing becomes the stop, and the trade gets stopped out by noise). The hybrid takes the wider of the two, honoring structure while ensuring the stop is "wide enough" to survive ordinary noise.

`1.5 × ATR` is a standard multiplier used in many trading systems (Keltner channels, Chandelier exits). It's not the only choice; a future spec may tune it from outcome data (P6 calibration).

**Trade-off**: The hybrid is more complex than either pure approach. P2 keeps the complexity in a single function with explicit unit tests; the test suite asserts the invariant "stop is always on the correct side of entry" so any regression is caught.

### D5. Null fields produce penalties, not rejection

**Decision**: A scoring run that receives a snapshot with `null` derivatives fields emits the score with a `null_field_penalty` per missing field (max deduction 10 per field, total penalty capped at 30). The score is never rejected.

**Rationale**: P1 deliberately ships nullable fields because the constitution says the system "MUST model" derivatives context "when available" (Constitution III). "When available" implies a graceful degradation path when the data isn't there. Rejecting the entire scoring run on one missing field would be brittle and would bias the system toward venues that provide all data points — the opposite of multi-asset coverage (Constitution III).

A penalty of 10 per missing field (capped at 30) means:
- All 9 derivatives fields present: 0 penalty
- 1 field null: -10 (score is 0-90, not catastrophic)
- 2-3 fields null: -20 to -30 (score is 0-80, still potentially tradeable but penalized)
- 4+ fields null: capped at -30 (the system "knows" it's flying blind)

The cap at 30 prevents a single missing field from dominating the score. The component that requires the missing field is marked `data_sufficient: false` so the audit trail is clear.

**Trade-off**: A penalty is gentler than a veto. If you'd rather have a hard veto on a critical missing field (e.g., no `last_price` → no trade), that's a future-spec concern. P2 prefers permissive scoring with explicit penalties.

### D6. RiskPlan only for the recommended side

**Decision**: The score first determines a directional lean (`long` / `short` / `neutral`); the `RiskPlan` is derived only for the recommended side. If `neutral`, no `RiskPlan` is emitted and the `scoring_output` carries `risk_plan: null` plus a `rejection_reason`.

**Rationale**: A `RiskPlan` for both sides is a "phantom plan" — it tells the trader "here's how to trade long and here's how to trade short" without a directional commitment. That contradicts Constitution I (selectivity) and the P0 FR-005 requirement that risk plans are "independently derived from alert text" — there is no alert yet, and a side-neutral RiskPlan is essentially an alert template.

The cleanest contract is: the score says `long`, the RiskPlan describes how to trade `long`. The trader (and P3) decide whether to act.

**Trade-off**: The scorer does twice the work if you want both sides (and discards half). This is fine for a personal-product scorer running a few snapshots per minute. Future P3 may add a "long + short scenarios" feature for traders who explicitly want both.

### D7. StrategyVersion v0.1.0 introduced in P2

**Decision**: A single `StrategyVersion` (`v0.1.0`, fingerprint = sha256 of the scoring rules table) is introduced. Every `ConfidenceScore` and `RiskPlan` references it. P3 may add `v0.2.0` if scoring logic changes.

**Rationale**: P0 FR-018 requires version references. P0 Invariant 8 says versions are immutable. P2 ships the first version, frozen, and never mutates. A future spec that changes scoring logic MUST create `v0.2.0` and migrate the references in any new scoring output.

The fingerprint is the `sha256` of the canonical JSON serialization of the rules table. This is mechanical: the same rules always produce the same fingerprint, and a one-character change to a rule produces a different fingerprint.

**Trade-off**: A frozen rules table is rigid. If you want to tune a threshold, you have to bump the version. That's the point — the constitution requires versioned changes, not silent ones.

### D8. NumPy for math, stdlib for everything else

**Decision**: NumPy is the only math library. Stdlib `logging` for diagnostics. Stdlib `argparse` for CLI. No `loguru`, no `structlog`, no `click`, no `typer`, no `pydantic`.

**Rationale** (full reasoning in P1's C12 discussion, which P2 inherits): every CPU-bound operation in P2 (math, indicator math, vectorized comparisons) has a NumPy implementation. The rest is glue. Adding more libraries increases the dependency surface without adding capability.

**Trade-off**: NumPy is a heavy dependency (~30 MB installed). For a personal product with 4 small math modules, it's overkill in lines-of-code terms. But NumPy is the ecosystem standard, and P5+ will use it heavily (Polars, pandas, scikit-learn all depend on NumPy semantically). P2 adds it now to avoid a transitive reshuffle later.

### D9. Decimal strings on output, float64 internally

**Decision**: All money-like fields in the scoring output (`entry_zone`, `stop_loss`, `take_profit`, R-multiples) are decimal strings with 8 decimal places. Internally, math runs on `np.float64`. The `to_decimal_string` helper is the single source of truth for formatting.

**Rationale**: P0 Invariant 2 (in `spec-001/data-model.md`) says "money-like fields use `Decimal`-compatible string representation in JSON; never `float`". This invariant carries through to P2. 8 decimal places is more than enough for crypto precision (most coins trade at $0.0000001 granularity; 8 places covers BTC satoshis and ETH gwei boundaries).

The math is float64 internally because (a) NumPy doesn't have a built-in decimal type, (b) the math is finite-precision, and (c) the 8-place output rounding is tighter than the float64 mantissa for the values we compute. We are not losing information in practice.

**Trade-off**: A future spec may move to `decimal.Decimal` throughout, but it requires either dropping NumPy or using a Decimal-aware NumPy shim. P2 keeps the simple path.

### D10. Three TP levels: 1R, 2R, 3R

**Decision**: The take-profit ladder has three levels. TP1 = 1R (covers the risk), TP2 = 2R, TP3 = 3R. R is the distance from entry to stop, expressed in the same units as the entry.

**Rationale**: A 1R/2R/3R ladder is a well-known pattern. The math is mechanical (multiply the R distance by 1, 2, 3). The R/R expectations array mirrors it (1.0, 2.0, 3.0). This makes the output auditable: a reviewer can read TP1 and verify it equals `entry + R` (for longs) or `entry - R` (for shorts).

The ladder is fixed at 3 levels. A future spec may add a 4th (e.g., 4R for "runner"), but P2 keeps it simple.

**Trade-off**: A fixed ladder ignores the structure of the trade (e.g., a resistance level at 1.5R is not in the ladder). P3 (signal generator) may add structure-aware TP placement on top of P2's output. P2 keeps it mechanical.

### D11. Determinism via no-rng and no-time

**Decision**: The scorer is a pure function. No `np.random` calls. No `datetime.now()`. No environment-dependent values. Same input → byte-identical output.

**Rationale**: P0's traceability principles and P1's C9 fixture determinism carry through. If a future spec introduces randomness (e.g., for Monte Carlo), it MUST be seeded and the seed MUST be a fixture field (so the result is still deterministic per fixture).

**Trade-off**: Pure functions are easy to test but lack state. P3 (signal generator) will be the stateful component; P2 stays pure.

## Open research questions (deferred)

These are intentionally NOT resolved in P2. They are recorded so the next phase knows what to investigate.

### R1. Funding carry scoring (deferred to P3+)

`funding_rate` is in the snapshot's derivatives context but P2 does not use it for scoring. A future spec may add a `funding_carry` component that penalizes setups where the trader would be paying funding (long in a high-positive-funding market). P2 keeps this door open by including the field in the snapshot's `derivatives_context` schema.

### R2. Liquidity suitability formula (deferred to P3+)

`liquidity_suitability` is `null` in P1 fixtures. P2 does not compute it. A future spec may define a formula (e.g., `volume × spread_inverse`) and add it to the snapshot. P2 keeps this door open by including the field in the `WatchlistAsset` schema.

### R3. Breakout detection (deferred to P3+)

P2's entry is swing-based, which misses breakouts. P3 (signal generator) may add a breakout-detection layer on top of P2's swing-based output. P2 does not attempt to detect breakouts.

### R4. ML-based scoring (deferred to P9+ at the earliest)

ML-based scoring is allowed by the constitution but requires a calibration spec (P6), outcome data (P5), and a dedicated review. P2 is the rules-based baseline. A future ML scorer would replace or augment P2's `ConfidenceScore` with a model output, but only after a calibration spec shows that the ML model outperforms the rules-based baseline on historical data.

### R5. Cross-asset confluence (deferred to P7+)

A single scoring run on BTC does not consider ETH or SOL. Cross-asset confluence (e.g., "BTC trend + ETH alignment = stronger setup") is a future spec. P2 scores one snapshot at a time.

### R6. Multi-strategy / portfolio scoring (deferred to P9+)

P2 produces a single score per snapshot. A future spec may support multiple strategies (e.g., trend-following, mean-reversion, breakout) and produce multiple scores per snapshot. P2 keeps the contract simple.

### R7. Calibration of weights from outcomes (deferred to P6)

P2's component weights (default 0.40 / 0.30 / 0.30 for trend_alignment / volatility_suitability / structural_clarity) are hand-tuned. P6 (calibration) may adjust them based on outcome data. P2 ships fixed weights; P6 tunes them.

### R8. ATR multiplier tuning (deferred to P6)

P2's `1.5 × ATR` stop multiplier is a default. P6 may tune it from outcome data. P2 ships the default.

## Summary

P2 is intentionally small. 3 components, 4 modules, 1 CLI, 1 validator, 1 test suite. The design decisions above explain why each shape is what it is. The open research questions are documented so the next phases know what to investigate, but they do NOT block P2.

The scoring engine is a pure function. The CLI wraps it. The tests assert its invariants. The fixtures prove it works on P1's input. P3 will turn its output into signals.
