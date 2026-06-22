# Specification Quality Checklist: Scoring Engine v1 (P2)

**Purpose**: Validate specification completeness and quality before proceeding to PR review.
**Created**: 2026-06-21
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details that would couple the contract to a specific runtime (P2 is intentionally language-agnostic at the contract level; the runtime is one allowed implementation).
- [x] Focused on user value and business needs (next-phase developers need a decomposable confidence score and a derivable risk plan).
- [x] Written for non-technical stakeholders where possible (the spec is about scoring rules, not code).
- [x] All mandatory sections completed (User Scenarios, Functional Requirements, Key Entities, Success Criteria, Assumptions).

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain.
- [x] Requirements are testable and unambiguous.
- [x] Success criteria are measurable (exit codes, line counts, score ranges, byte sizes, grep results, runtime budgets).
- [x] Success criteria are technology-agnostic where possible; the one explicit Python 3.11+ / NumPy / pytest / hypothesis mention is documented as a clarification (C8, C9) and is intentional.
- [x] All acceptance scenarios are defined.
- [x] Edge cases are identified (missing timeframes, unknown regime, partial null fields, funding rate non-zero, ATR floor violation, etc.).
- [x] Scope is clearly bounded (no live data, no ingestion, no signal generation, no execution, no ML).
- [x] Dependencies and assumptions identified (Python 3.11+, `uv`, NumPy 2.x, pytest 8.x, hypothesis 6.x).

## Feature Readiness

- [x] All functional requirements (FR-001 through FR-020) have clear acceptance criteria or are testable via pytest.
- [x] User scenarios cover primary flows (score decomposition, risk plan derivation, no-trade rejection, version attribution).
- [x] Feature meets measurable outcomes defined in Success Criteria (SC-001 through SC-010 are all verifiable in this spec).
- [x] No implementation details leak into the spec that would prevent the next phase from choosing a different runtime.

## Constitutional Compliance

- [x] Re-evaluation of the 7 constitution principles recorded in `plan.md` Constitution Check.
- [x] All 7 principles addressed; no violations.
- [x] No complexity exceptions required.

## Traceability

- [x] Every FR (FR-001..FR-020) is referenced from at least one of: `plan.md`, `data-model.md`, `research.md`, `quickstart.md`, or the scorer code.
- [x] Every SC (SC-001..SC-010) is referenced from at least one of: `plan.md`, `data-model.md`, `quickstart.md`, or the scorer code.
- [x] The 18 clarifications (C1..C18) are listed in `spec.md` and traced to the design decisions in `research.md`.

## Reproducibility

- [x] `quickstart.md` documents the exact `uv` commands to set up the venv and install runtime + dev deps.
- [x] The 8-line self-check in `quickstart.md` can be run on a clean clone in under 30 seconds.
- [x] The validator is fully deterministic: same inputs produce same output and exit code across runs.
- [x] The scorer is a pure function: same snapshot input produces byte-identical output.

## Test Coverage

- [x] `pytest` runs clean: 70/70 pass, 0 failures, 0 errors.
- [x] Property-based tests exercise at least 100 examples per property (hypothesis default).
- [x] Coverage of `scripts/scoring/` modules: strategy_version, regime_classifier, confluence, risk_plan, score.
- [x] End-to-end test: scoring runs successfully on all 3 P1 fixtures and produces 3 valid `ScoringOutput` JSONs.

## Notes

- Validation pass 1: The spec is ready for PR review.
- No open [NEEDS CLARIFICATION] markers remain.
- The 18 clarifications were resolved in a single session on 2026-06-21 before the spec was authored; they are recorded in `spec.md` so the rationale is preserved.
- This spec produces the first runtime math for crypto-alpha. The scorer is a pure function. The CLI wraps it. The tests assert its invariants. The fixtures prove it works on P1's input.
- A `[NEEDS CLARIFICATION]` count of zero is a hard prerequisite for opening the PR. The count is 0.
- Constitutional compliance is verified by the explicit checklist in `plan.md` and re-verified here.
- During implementation, one design decision was refined: the regime classifier was originally specified to re-classify from price action; in practice this overrode P1's carefully-constructed fixture regimes. The implementation trusts non-unknown input regimes and re-classifies only when the input is `unknown`. This is documented in the classifier's docstring and reflected in the test suite.
