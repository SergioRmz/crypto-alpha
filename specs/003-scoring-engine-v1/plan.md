# Implementation Plan: Scoring Engine v1

**Branch**: `003-scoring-engine-v1` | **Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-scoring-engine-v1/spec.md` (with 18 clarifications resolved in-session on 2026-06-21). This is the P1 → P2 handoff defined in `specs/001-profitable-trading-decision-domain/plan.md` (Domain Phasing table, P2 row), consuming the P1 data layer (delivered in `specs/002-data-layer/`) as test input.

**Note**: This plan documents the first runtime scoring engine for crypto-alpha. It introduces NumPy-based math, a property-based test suite, and a CLI. It does NOT introduce live data, signals, alerts, manual trade journal, outcomes, or learning.

## Summary

Implement a deterministic, auditable, rules-based scoring engine that consumes a `MarketContextSnapshot` (P1) and produces a `ScoringOutput` containing a decomposable `ConfidenceScore` (3 named components + penalty array + total_score in 0-100) and an optional `RiskPlan` (swing-based entry, hybrid ATR+swing stop, 1R/2R/3R take-profit ladder). The engine is a function — no I/O, no async, no service. The CLI wraps it for ergonomics. The test suite uses `pytest` + `hypothesis` to assert math invariants.

## Technical Context

- **Language/Version**: Python 3.11+ (inherited from P1; in `pyproject.toml` `requires-python`).
- **Primary Dependencies**:
  - `jsonschema>=4.0,<5.0` (P1, for the scoring-output validator)
  - `numpy>=2.0,<3.0` (P2 new, for math)
  - `pytest>=8.0,<10.0` (P2 new, for test runner)
  - `hypothesis>=6.0,<7.0` (P2 new, for property-based tests)
- **Storage**: None. Scored outputs are written to stdout or a file path. No persistence.
- **Testing**: `pytest` + `hypothesis`. Property-based tests per math module. Coverage target ≥ 80% lines on `scripts/scoring/`.
- **Target Platform**: Developer workstation, Linux-first. No server, no cloud, no deployment.
- **Project Type**: Library + CLI. The library (`scripts/scoring/`) is importable; the CLI (`scripts/scoring/score.py`) is the user-facing surface.
- **Performance Goals**: A single scoring run on a snapshot completes in under 50 ms (typical: < 5 ms on commodity hardware). The 60-second budget in SC-010 is dominated by pytest execution, not by the scorer itself.
- **Constraints**:
  - No external network access required (and no live data allowed).
  - No secrets, no credentials, no live URLs in any P2 artifact.
  - Output is fully deterministic: same input → byte-identical output.
  - All money-like fields in the output are decimal strings, never `float`.
  - Math runs on `np.float64` internally with explicit rounding to 8 decimal places on output.
- **Scale/Scope**: One scorer, three modules, one CLI, one validator, one test suite. ~500 LOC of runtime code, ~300 LOC of tests. Total artifact size under 200 KB.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Risk-Adjusted Profitability Over Signal Volume (I)**: P2 explicitly enforces selectivity. The `regime_veto` mechanism (FR-004) forces `total_score = 0` and `risk_plan = null` on 4 of the 8 regimes. The `tradable_floor` (50.0) rejects low-conviction setups. "No-trade" is a first-class output, not an error.
- [x] **Spec-Driven, Iteration-Bounded Delivery (II)**: This spec IS spec-driven. Scope is locked to scoring + risk plan. Signals, alerts, journal, outcomes, learning, calibration are explicitly deferred to P3+.
- [x] **Futures-First, Multi-Asset Opportunity Intelligence (III)**: The scorer is asset-agnostic. It accepts any `MarketContextSnapshot`. P1's BTC/ETH/SOL fixtures are the test surface; a future asset is just another snapshot. The `canonical_symbol` is preserved through the `snapshot_ref` in `ScoringOutput`.
- [x] **Traceable Decisions and Auditable Intelligence (IV)**: Every `ConfidenceScore` references a `StrategyVersion` (v0.1.0 in P2). Every component has `name`, `raw_value`, `max_value`, `weight`, `contribution`, `data_sufficient`. Every penalty has `name`, `deduction`, `reason`. The `StrategyVersion` fingerprint is `sha256(strategy_rules_table)`, so the version's identity is mechanical.
- [x] **Manual-First Execution, Automation-Compatible Architecture (V)**: P2 does not produce signals. P2's output is `ScoringOutput`, which P3 will turn into a `Signal` (and only after a human review step in the manual-first workflow). `ExecutionIntent` remains read-only in P2.
- [x] **Learning Requires Evidence, Versioning, and Guardrails (VI)**: `StrategyVersion` is created once and never mutated (P0 Invariant 8). The `v0.1.0` rules table is frozen at the module level. A future spec that changes scoring logic MUST create `v0.2.0`; old fixtures referencing `v0.1.0` remain valid.
- [x] **Industrial Maintainability for Personal Use (VII)**: Modular structure (`regime_classifier`, `confluence`, `risk_plan`, `score` are separate modules). No secrets, no live data. Validation is reproducible. Output is deterministic.

**No constitution violations, no complexity exceptions required.**

## Project Structure

### Documentation (this feature)

```text
specs/003-scoring-engine-v1/
├── spec.md                # Feature specification (with 18 clarifications)
├── plan.md                # This file
├── research.md            # Phase 0: math design decisions and precedent scan
├── data-model.md          # Phase 1: field-level precision for the 3 output schemas
├── quickstart.md          # Phase 1: how to reproduce scoring from a clean clone
├── tasks.md               # Phase 2: concrete implementation tasks
├── checklists/
│   └── requirements.md    # Spec quality gate
├── contracts/             # Phase 1: JSON Schemas for scorer output
│   ├── confidence-score.schema.json
│   ├── risk-plan.schema.json
│   └── scoring-output.schema.json
└── fixtures/              # Phase 1: scored outputs derived from P1 fixtures
    ├── btc-scored.json
    ├── eth-scored.json
    └── sol-scored.json
```

### Source Code (repository root)

```text
scripts/
├── scoring/
│   ├── __init__.py
│   ├── score.py              # CLI entrypoint + public API
│   ├── regime_classifier.py  # rules-based regime re-classification
│   ├── confluence.py         # 3-component math
│   ├── risk_plan.py          # entry/SL/TP/R derivation
│   └── strategy_version.py   # StrategyVersion v0.1.0 + rules table
└── validation/
    └── validate_scoring.py   # validator for scored-* fixtures (and the CLI's validate subcommand)

tests/
└── scoring/
    ├── __init__.py
    ├── test_regime_classifier.py
    ├── test_confluence.py
    ├── test_risk_plan.py
    └── test_strategy_version.py
```

**Structure Decision**: A flat `scripts/scoring/` package. No `src/` layout because the project is still small and the import path `scripts.scoring` is explicit. A future spec may migrate to `src/alpha_signal/scoring/` if the project grows.

## Domain Phasing

P2 is the second runtime handoff. It does not produce a running system; it produces **the math + the contract for the math's output**. The phasing within P2 is:

| Step | Output | Depends on |
|---|---|---|
| 1. Research | `research.md` | spec.md |
| 2. Data model | `data-model.md` | research.md |
| 3. Schemas | 3 `*.schema.json` files | data-model.md |
| 4. Strategy version | `scripts/scoring/strategy_version.py` | data-model.md |
| 5. Regime classifier | `scripts/scoring/regime_classifier.py` + tests | strategy_version, P1 fixtures |
| 6. Confluence math | `scripts/scoring/confluence.py` + tests | strategy_version, regime output |
| 7. Risk plan derivation | `scripts/scoring/risk_plan.py` + tests | strategy_version, confluence output |
| 8. CLI | `scripts/scoring/score.py` | confluence, risk_plan |
| 9. Fixtures | 3 `*-scored.json` files | CLI run on P1 fixtures |
| 10. Validator | `scripts/validation/validate_scoring.py` | schemas + fixtures |
| 11. Quickstart | `quickstart.md` | all of the above |
| 12. Quality gate | `checklists/requirements.md` | spec.md + plan.md |
| 13. Self-check | run scorer + pytest + validator + FR/SC coverage | all artifacts |

After P2, the next spec (P3: signal generator + alert format) will:
- Consume the `ScoringOutput` fixtures as test inputs.
- Reference the `ConfidenceScore` and `RiskPlan` schemas as contracts.
- Add the `Signal` entity and the alert rendering.
- NOT modify any P2 artifact without an amendment.

## Risk and Guardrails (carried into later specs)

- **No live data.** The scorer is a pure function on a snapshot. No I/O, no sockets, no time.
- **No silent rule changes.** Any change to the `strategy_rules_table` MUST create `StrategyVersion` v0.2.0; v0.1.0 fixtures remain valid.
- **No opaque confidence.** Every `ConfidenceScore` is a structure. `total_score` is derived, not stored. `components[]` is non-empty and explicitly named.
- **No advisory language in risk plan.** `risk_plan.notes` is free text, MUST NOT contain buy/sell/hold language (Constitution I).
- **No `float` in money fields.** Decimal strings only. The `to_decimal_string` helper is the single source of truth.
- **No new external runtime deps beyond NumPy, pytest, hypothesis.** If a future spec needs more, it MUST justify the addition in its own `plan.md` and bump this constraint explicitly.
- **No ML.** P2 is rules-based with hand-tuned thresholds. ML-based scoring is a future spec, gated by a calibration spec (P6) and a dedicated review.

## Complexity Tracking

No constitution violations, no complexity exceptions. The scoring engine is intentionally minimal: 4 small modules, 1 CLI, 1 validator, 1 test suite. Total addition to the repo: ~500 LOC of runtime code + ~300 LOC of tests + 3 schemas + 3 fixtures.

## Validation Evidence Targets (to be recorded in `quickstart.md`)

- `uv` venv creation time (with P2 deps added)
- `pytest` execution time and pass count
- Validator run time and exit code
- Scorer run time per fixture (target: < 50 ms)
- `OK` line count from validator
- `grep` for secrets: 0 matches
- `grep` for `[NEEDS CLARIFICATION]` in this spec: 0 matches
- Coverage report: ≥ 80% lines on `scripts/scoring/`
