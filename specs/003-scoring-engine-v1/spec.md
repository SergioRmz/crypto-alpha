# Feature Specification: Scoring Engine v1

**Feature Branch**: `003-scoring-engine-v1`

**Created**: 2026-06-21

**Status**: Draft

**Input**: User description: "Implement the P2 scoring engine for crypto-alpha: a rules-based, deterministic, auditable pipeline that consumes a `MarketContextSnapshot` (from spec 002) and produces a decomposable `ConfidenceScore` plus a derived `RiskPlan`, classified under a `StrategyVersion` v0.1.0. The pipeline must be reproducible from the same inputs, the math must be unit-tested with property-based tests, and the output must be a JSON Schema-validated artifact. No live data, no signal generation, no alerts, no execution, no ML, no manual trade journal — strictly score + risk plan from snapshot."

## Clarifications

### Session 2026-06-21

The following design decisions were resolved before authoring this spec, in alignment with the P0 constitution and the P1 → P2 handoff defined in `spec-001/plan.md`.

- **C1 — Confidence components in v1**: Exactly **3 components** in v1: `trend_alignment` (multi-timeframe agreement), `volatility_suitability` (vol regime matches holding horizon), `structural_clarity` (whether price action is tradeable vs choppy). Penalties layer on top: `null_field_penalty`, `regime_veto`. Later specs may add `funding_carry` and `liquidity_context` when their inputs become reliable. *(Resolves B1.)*
- **C2 — Regime classifier is rules-based**: The classifier uses a fixed table of thresholds on `realized_volatility_pct`, `atr_pct`, and price action (gains/loses over 1h and 4h bars). No ML, no learned weights. Every rule is a one-liner with a unit test. *(Resolves B2.)*
- **C3 — Entry zone is swing-based**: `entry_zone` is derived from the most recent swing high/low on the dominant timeframe (1h for v1). The score recommends `long` if `close > swing_low + 0.5 × range` and `short` if `close < swing_high - 0.5 × range`. *(Resolves B3.)*
- **C4 — Stop loss is hybrid (ATR + swing)**: `stop_loss` = `entry ± max(1.5 × ATR, |entry - swing_extreme|)`. The more conservative of the two is chosen. This honors "stop-loss is identifiable in market structure, not arbitrary" (P0 Q1) while remaining mechanical. *(Resolves B4.)*
- **C5 — Null fields produce penalties, not rejection**: A scoring run that receives a snapshot with `null` derivatives fields emits the score with a `null_field_penalty` per missing field (max deduction 10 per field, total penalty capped at 30). The score is never rejected. Components that require the missing field are marked `data_sufficient: false` in the output. *(Resolves B5.)*
- **C6 — RiskPlan is computed for the recommended side only**: The score first determines a directional lean (`long` / `short` / `neutral`); the `RiskPlan` is derived only for the recommended side. If `neutral`, no `RiskPlan` is emitted and the `scoring_output` carries `risk_plan: null` plus a `rejection_reason`. This avoids the "phantom plan" problem and is the cleanest handoff to P3 (which decides whether to emit a signal). *(Resolves B6.)*
- **C7 — StrategyVersion v0.1.0 is created in P2**: A single `StrategyVersion` (`v0.1.0`, fingerprint = sha256 of the scoring rules table) is introduced. Every `ConfidenceScore` and `RiskPlan` references it. P3 may add a `v0.2.0` if scoring logic changes. *(Resolves B7.)*
- **C8 — Math library is NumPy**: NumPy is the math library. It is the de-facto standard, deterministic for the operations we use (`np.std`, `np.mean`, vectorized comparisons), and is already in the project's transitive path for future P5+ work. Float64 is acceptable internally because all money-like fields are formatted as decimal strings on output. *(Confirms D1.)*
- **C9 — Test stack: pytest + hypothesis**: `pytest` for unit tests, `hypothesis` for property-based tests on math invariants (e.g., R/R always ≥ 0 for valid inputs; stop_loss is always on the correct side of entry; total_score is always in 0-100). *(Confirms D2.)*
- **C10 — Logging: stdlib logging**: No `loguru`, no `structlog`. Stdlib `logging` with INFO default. *(Confirms D3.)*
- **C11 — CLI: argparse + stdlib**: No `click`, no `typer`. Two subcommands: `score <snapshot.json>` (stdout JSON) and `validate <scored.json>` (exit code). *(Confirms D4.)*
- **C12 — New runtime dependencies**: `numpy`, `pytest`, `hypothesis`. All declared in `pyproject.toml`. No other new deps. *(Confirms D5.)*
- **C13 — Branch and directory**: Branch `003-scoring-engine-v1`. Spec dir `specs/003-scoring-engine-v1/`. *(Confirms D6.)*
- **C14 — Determinism guarantee**: Given identical snapshot input, the scorer MUST produce byte-identical output across runs. To achieve this, NumPy is used with no `np.random` calls anywhere; all math is deterministic on the input. The CLI writes JSON with sorted keys and a fixed float-formatting helper for decimal strings.
- **C15 — Decimal strings on output, float64 internally**: All money-like fields in the scoring output (`entry_zone`, `stop_loss`, `take_profit`, R-multiples) are decimal strings. Internally, math runs on `np.float64`. The `to_decimal_string` helper rounds to 8 decimal places (sufficient for crypto precision, no float artifacts).
- **C16 — Risk plan rejection criteria**: A scoring run emits `risk_plan: null` when ANY of: (a) the regime is `chop`, `manipulation_probable`, `extreme_volatility`, or `low_liquidity`; (b) the recommended side's stop would be inverted vs entry (math failure); (c) the score is below the `tradable_floor` (50.0 in v1). Otherwise the risk plan is emitted with full structure.
- **C17 — Take-profit ladder**: Three TP levels in v1: TP1 = 1R (covers risk), TP2 = 2R, TP3 = 3R. All three are computed relative to the chosen stop distance. Partial exit guidance is documented in `risk_plan.notes` as a comment (e.g., "consider partial exit at TP1"), not as a directive.
- **C18 — Score bucket boundaries**: `0-50` (no trade), `50-70` (low conviction), `70-80` (medium), `80-90` (high), `90-100` (exceptional). The bucket is derived, not stored.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Score a snapshot and decompose the score (Priority: P1)

As the next-phase developer, I want to feed a `MarketContextSnapshot` to the scoring engine and receive a `ConfidenceScore` that is decomposable into named components and penalties so that I can audit *why* a score is what it is.

**Why this priority**: A confidence score that cannot be decomposed is a black box. Constitution IV requires traceable, auditable intelligence. Without decomposition, P6 (calibration) is impossible.

**Independent Test**: Can be fully tested by running the scorer on a known P1 fixture (e.g., `btc-perp-snapshot.json`), reading the `confidence_score.components[]` array, and verifying that each component has a name, a raw value, a max value, a weight, and a contribution — and that the sum of weighted contributions matches the `total_score` within rounding tolerance.

**Acceptance Scenarios**:

1. **Given** a BTC snapshot, **When** the scorer runs, **Then** the output `confidence_score.components` array has exactly 3 entries (`trend_alignment`, `volatility_suitability`, `structural_clarity`), each with `name`, `raw_value`, `max_value`, `weight`, `contribution`.
2. **Given** a scoring run, **When** the total_score is computed, **Then** `total_score = sum(component.contribution) - sum(penalty.deduction)`, and the result is in `[0, 100]`.
3. **Given** a scoring run with `null` derivatives fields, **When** the output is read, **Then** a `null_field_penalty` exists per missing field and the component that requires that field is marked `data_sufficient: false`.
4. **Given** a scoring run on a snapshot whose `regime == "chop"`, **When** the output is read, **Then** a `regime_veto` penalty of 100 is applied (forcing `total_score = 0`) and the `risk_plan` is `null`.

---

### User Story 2 - Derive a risk plan from a scored snapshot (Priority: P1)

As the next-phase developer, I want the scoring engine to emit a `RiskPlan` with entry zone, stop loss, take-profit ladder, and R/R expectations so that P3 (signal generator) can convert it into a `Signal` without re-running the math.

**Why this priority**: P0 FR-005 mandates that risk plans are derived independently from alert text. P3 cannot proceed without a stable `RiskPlan` schema and a working derivation.

**Independent Test**: Can be fully tested by scoring a snapshot whose regime is not vetoed, then verifying the `risk_plan` has `entry_zone`, `stop_loss`, `take_profit_plan[]` with exactly 3 TPs, `risk_reward_expectations[]` with one R/R per TP, and a `max_intended_holding_period` of "1d" or shorter.

**Acceptance Scenarios**:

1. **Given** a non-vetoed scoring run, **When** the output is read, **Then** `risk_plan` is non-null and contains all required P0 fields.
2. **Given** a `RiskPlan` with `direction: long`, **When** `entry_zone` and `stop_loss` are inspected, **Then** `stop_loss < entry_zone` and the distance is at least 1.5 × ATR.
3. **Given** a `RiskPlan` with TP1/TP2/TP3, **When** the R/Rs are inspected, **Then** they are exactly 1.0, 2.0, and 3.0 (relative to the stop distance), and `risk_reward_expectations` reflects the same.
4. **Given** a `RiskPlan`, **When** `max_intended_holding_period` is read, **Then** it is one of `"1m"`, `"5m"`, `"15m"`, `"1h"`, `"4h"`, `"1d"` (P0 intraday-to-multi-day constraint).

---

### User Story 3 - Reject a non-tradeable setup (Priority: P1)

As the next-phase developer, I want the scoring engine to refuse to emit a `RiskPlan` (and force `total_score` to 0) when the regime vetoes trading, so that downstream specs and the human trader never see a phantom plan on a setup the system has already decided is un-tradeable.

**Why this priority**: P0 FR-015 mandates that "no-trade" is a first-class outcome. Constitution I (selectivity) requires it. P0 Q1 lists 4 veto regimes explicitly.

**Independent Test**: Can be fully tested by scoring a snapshot whose regime is one of the 4 veto regimes, then verifying the output has `risk_plan: null`, a `regime_veto` penalty of 100, and a `rejection_reason` string.

**Acceptance Scenarios**:

1. **Given** a snapshot with `regime: chop`, **When** the scorer runs, **Then** `risk_plan` is `null` and `rejection_reason` mentions the regime.
2. **Given** a snapshot with `regime: extreme_volatility`, **When** the scorer runs, **Then** `risk_plan` is `null` and the `total_score` is exactly 0.
3. **Given** a vetoed scoring run, **When** the output is read, **Then** the `scoring_output` is still a valid schema-conformant artifact (it is a "no-trade" output, not a parse error).

---

### User Story 4 - Version every score and risk plan (Priority: P2)

As the next-phase developer, I want every `ConfidenceScore` and `RiskPlan` to reference a `StrategyVersion` so that the system's behavior at decision time is always explainable against the rules that produced it.

**Why this priority**: Constitution IV requires traceable decisions. P0 FR-018 requires version references. Without `StrategyVersion`, P5 (outcome capture) and P6 (calibration) cannot reliably attribute performance to a specific scoring logic.

**Independent Test**: Can be fully tested by running the scorer on a snapshot, reading the `confidence_score.strategy_version_ref` and `risk_plan.strategy_version_ref`, and verifying both equal `"v0.1.0"` and the version's fingerprint matches `sha256(strategy_rules_table)`.

**Acceptance Scenarios**:

1. **Given** any scoring run, **When** the output is read, **Then** both `confidence_score.strategy_version_ref` and `risk_plan.strategy_version_ref` (when risk_plan is non-null) are `"v0.1.0"`.
2. **Given** a future spec introduces a `v0.2.0` rule change, **When** the scorer is re-run, **Then** new outputs reference `v0.2.0`, and old fixtures that reference `v0.1.0` are unchanged.

---

### Edge Cases

- All 6 timeframes are present but one has a `null` bar (data freshness). The scorer must not crash; the affected timeframe is excluded from `trend_alignment` with a `null_field_penalty` on the component.
- The snapshot has `regime: unknown` (P1 fixtures set this when no classifier has run). The scorer must NOT apply a regime veto, but MUST apply a `regime_unknown_penalty` of 15 to acknowledge the unclassified state.
- The snapshot's `last_price` is `null` but `mark_price` is present. The scorer uses `mark_price` for entry calculation, and a `null_field_penalty` of 5 is applied.
- The snapshot's `funding_rate` is non-zero (longs are paying shorts or vice versa). The scorer logs the funding rate in the output's `notes` field but does NOT use it for the score (P2 does not own funding-based scoring; that is a later spec).
- The recommended side's stop is closer to entry than 1 × ATR (very tight structure). The scorer widens the stop to `1.5 × ATR` minimum and notes the widening in `risk_plan.notes`.
- The recommended side's stop is on the wrong side of entry (math failure from a near-zero ATR). The scorer applies a `safety_veto` and returns `risk_plan: null` with a `rejection_reason` mentioning ATR.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST consume a `MarketContextSnapshot` JSON conforming to `specs/002-data-layer/contracts/snapshot.schema.json` and produce a `ScoringOutput` JSON conforming to `specs/003-scoring-engine-v1/contracts/scoring-output.schema.json`.
- **FR-002**: System MUST compute a `ConfidenceScore` with exactly 3 components (`trend_alignment`, `volatility_suitability`, `structural_clarity`) and a penalty array.
- **FR-003**: System MUST produce a `total_score` in `[0, 100]` equal to `clamp(sum(component.contribution) - sum(penalty.deduction), 0, 100)`.
- **FR-004**: System MUST apply a `regime_veto` penalty of 100 (forcing `total_score = 0` and `risk_plan = null`) when the snapshot's `regime` is one of `chop`, `manipulation_probable`, `extreme_volatility`, `low_liquidity`.
- **FR-005**: System MUST apply a `regime_unknown_penalty` of 15 when the snapshot's `regime` is `unknown` and no regime veto is otherwise triggered.
- **FR-006**: System MUST emit a `null_field_penalty` per `null` field in the snapshot's derivatives context (max deduction 10 per field, total penalty capped at 30).
- **FR-007**: System MUST derive a directional lean (`long` / `short` / `neutral`) from the snapshot's price action and emit a `RiskPlan` only for the recommended side.
- **FR-008**: System MUST compute `entry_zone` as the swing-based reference (C3) and `stop_loss` as the hybrid ATR+swing reference (C4) for the recommended side.
- **FR-009**: System MUST emit a 3-level take-profit ladder (TP1=1R, TP2=2R, TP3=3R) and the corresponding `risk_reward_expectations[]`.
- **FR-010**: System MUST set `max_intended_holding_period` to the dominant timeframe's horizon (`1h` in v1).
- **FR-011**: System MUST reference `StrategyVersion` v0.1.0 in every `ConfidenceScore` and every non-null `RiskPlan`.
- **FR-012**: System MUST be fully deterministic: identical snapshot input MUST produce byte-identical output across runs.
- **FR-013**: System MUST use NumPy for math and stdlib `logging` for diagnostics. No `loguru`, no `structlog`.
- **FR-014**: System MUST format all money-like fields in the output as decimal strings (8 decimal places), never as `float`.
- **FR-015**: System MUST NOT call any external network endpoint or live data source.
- **FR-016**: System MUST NOT produce a `Signal` entity. The output is `ScoringOutput` only; P3 owns the signal format.
- **FR-017**: System MUST emit a `rejection_reason` string when `risk_plan` is `null`. The string MUST name the veto or threshold that triggered the rejection.
- **FR-018**: System MUST be exercised by a `pytest` test suite covering: regime classifier rules, confluence math invariants, risk plan invariants (R/R, stop direction, ATR floor), null-field penalties, regime vetoes, and determinism.
- **FR-019**: System MUST include at least one property-based test using `hypothesis` per math module, asserting invariants that must hold across all valid inputs (e.g., R/R ≥ 0, stop on correct side, total_score in [0,100]).
- **FR-020**: System MUST provide a `scripts/scoring/score.py` CLI with two subcommands: `score <snapshot.json>` (writes ScoringOutput to stdout) and `validate <scored.json>` (validates against the output schemas and exits 0/1).

### Key Entities *(include if feature involves data)*

- **ConfidenceScore** *(P0 entity, schema-anchored in P2)*: A decomposable confidence assessment with exactly 3 components in v1, a penalty array, a `total_score` in 0-100, a `bucket`, and a `strategy_version_ref`.
- **RiskPlan** *(P0 entity, schema-anchored in P2)*: The derived trade management structure with `entry_zone_or_condition`, `stop_loss`, `take_profit_plan[]` (3 levels), `risk_reward_expectations[]` (one R/R per TP), `max_intended_holding_period`, and `invalidation_criteria`.
- **StrategyVersion** *(P0 entity, instantiated in P2)*: An immutable reference to the scoring rules table. v0.1.0 is the only version in P2.
- **ScoringOutput** *(P2-introduced)*: A wrapper that ties a `snapshot_ref` to a `confidence_score` and an optional `risk_plan`, with a `rejection_reason` when the run is a no-trade.
- **RegimeRulesTable** *(P2-introduced, internal)*: A frozen table of thresholds and rules used by the regime classifier. The fingerprint (sha256 of the canonical JSON) is the version's identity.
- **Penalties** *(P2-introduced)*: The set of named penalty types in v1: `null_field_penalty`, `regime_veto`, `regime_unknown_penalty`, `safety_veto` (ATR floor violation). Each has a `name`, `deduction`, and `reason`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `score <btc-perp-snapshot.json>` produces a `ScoringOutput` that passes `validate_scoring.py` with exit 0. Same for ETH and SOL fixtures.
- **SC-002**: The `ConfidenceScore.components[]` array has exactly 3 entries with `name`, `raw_value`, `max_value`, `weight`, `contribution`, and `data_sufficient`. No extras, no missing.
- **SC-003**: For every scored fixture, `total_score` is in `[0, 100]` and equals `clamp(sum(contribution) - sum(deduction), 0, 100)` within rounding tolerance (1e-6).
- **SC-004**: A `RiskPlan` with `direction: long` has `stop_loss < entry_zone`; with `direction: short` has `stop_loss > entry_zone`. The distance is at least 1.5 × ATR of the dominant timeframe.
- **SC-005**: A `RiskPlan` has exactly 3 TPs with R/Rs of exactly 1.0, 2.0, 3.0. `risk_reward_expectations[]` mirrors this.
- **SC-006**: A snapshot whose `regime` is `chop`, `manipulation_probable`, `extreme_volatility`, or `low_liquidity` produces `risk_plan: null` and a `rejection_reason` naming the regime.
- **SC-007**: Running the scorer twice on the same snapshot produces byte-identical output (excluding timestamp metadata in optional debug fields; v1 has no debug fields).
- **SC-008**: `pytest` runs clean: 0 failures, 0 errors. Property-based tests exercise at least 100 examples per property. Coverage of `scripts/scoring/` is ≥ 80% lines.
- **SC-009**: Zero secrets, credentials, API keys, or live URLs in any P2 artifact.
- **SC-010**: The full reproduction (venv setup, deps install, scorer run on 3 fixtures, pytest, validate) completes in under 60 seconds on commodity hardware.

## Assumptions

- Python 3.11+ is available (inherited from P1).
- `uv` is the canonical package manager (inherited from P1).
- The P1 fixtures (`specs/002-data-layer/fixtures/*.json`) are the inputs; the P2 fixtures (scored outputs) are derived from them and live under `specs/003-scoring-engine-v1/fixtures/`.
- The P1 schemas (snapshot, watchlist-asset, trading-universe) are stable at `schema_version: "0.1.0"`. A schema bump would require a new P2 spec.
- The scoring rules table is small and explicit; no rules file is loaded from disk. The table lives in `scripts/scoring/strategy_version.py` as a frozen module-level constant.
- The regime classifier does NOT call the existing P1 snapshot's `regime` field as ground truth; it RE-CLASSIFIES from the snapshot's price action and volatility data. The snapshot's `regime` is used only to detect veto and unknown states. *(This is a v1 simplification; a future spec may change the contract.)*
- "1.5 × ATR" and "1R/2R/3R" are P2 defaults. A future spec (P6 calibration) may tune these from outcome data, but P2 ships with fixed values.
- The P2 scorer is a function (`score(snapshot) -> ScoringOutput`), not a service. No I/O, no sockets, no async. CLI wrappers handle file I/O.
