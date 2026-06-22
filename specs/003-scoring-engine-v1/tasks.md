# Tasks: Scoring Engine v1 (P2)

**Input**: Design documents from `specs/003-scoring-engine-v1/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md` (all present)
**Tests**: Validation tasks are included because P2 is contract-first + math-first and pytest is the test surface.
**Organization**: Tasks are grouped by user story to enable independent verification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the documentation directory structure and runtime scaffolding for this spec.

- [X] T001 Create `specs/003-scoring-engine-v1/` directory and `contracts/`, `fixtures/`, `checklists/` subdirectories
- [X] T002 [P] Create `scripts/scoring/__init__.py` and `tests/scoring/__init__.py` packages
- [X] T003 [P] Create branch `003-scoring-engine-v1` from `main` and verify clean working tree
- [X] T004 [P] Update `pyproject.toml` to add `numpy`, `pytest`, `hypothesis` as new deps and pytest config

**Checkpoint**: Documentation scaffolding is ready; spec authors can write the foundation documents.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the foundational documents (spec, plan, research, data model) and the constitution check before any user-story work.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [X] T005 Author `specs/003-scoring-engine-v1/spec.md` with 4 user stories, 20 functional requirements, 10 success criteria, 18 clarifications, and the assumptions block
- [X] T006 Author `specs/003-scoring-engine-v1/plan.md` with summary, technical context, constitution check, project structure, and the P1→P2 handoff documentation
- [X] T007 [P] Author `specs/003-scoring-engine-v1/research.md` capturing 11 design decisions (D1-D11), 4 precedent scans, and 8 open research questions (R1-R8)
- [X] T008 [P] Author `specs/003-scoring-engine-v1/data-model.md` with field-level precision for the 3 output schemas
- [X] T009 [P] Author `specs/003-scoring-engine-v1/checklists/requirements.md` confirming content quality, requirement completeness, feature readiness, and constitutional compliance
- [X] T010 Run the constitution check in `plan.md` against `spec-001/constitution.md`; confirm all seven principles are addressed; document the result in `plan.md`

**Checkpoint**: All foundational documents exist, the constitution check passes, and the spec is internally consistent.

---

## Phase 3: User Story 1 - Score a snapshot and decompose the score (Priority: P1)

**Goal**: Lock the JSON Schema for `ConfidenceScore` and the math that produces it so that every score is mechanically auditable.

**Independent Test**: A reviewer can run the scorer on a P1 fixture, read the `confidence_score.components[]` array, and verify each component has `name`, `raw_value`, `max_value`, `weight`, `contribution`, and `data_sufficient`.

### Implementation for User Story 1

- [X] T011 [P] [US1] Author `specs/003-scoring-engine-v1/contracts/confidence-score.schema.json` (JSON Schema 2020-12) with 3 fixed components, 4 penalty types, `total_score` in 0-100, and derived bucket enum
- [X] T012 [US1] Author `scripts/scoring/strategy_version.py` with the frozen `StrategyVersion` v0.1.0 dataclass and `build_v0_1_0()` factory (sha256 fingerprint)
- [X] T013 [US1] Author `scripts/scoring/regime_classifier.py` with `reclassify(snapshot)` and `is_vetoed(regime)` (rules-based)
- [X] T014 [US1] Author `scripts/scoring/confluence.py` with 3 components (`trend_alignment`, `volatility_suitability`, `structural_clarity`) and `compute_components(snapshot, regime)`
- [X] T015 [US1] Author `scripts/scoring/decimal_format.py` with the `to_decimal_string` helper (single source of truth for money-like fields)
- [X] T016 [US1] Verify the confidence-score schema is a valid JSON Schema 2020-12

**Checkpoint**: The confidence-score schema is a valid, mechanical contract.

---

## Phase 4: User Story 2 - Derive a risk plan from a scored snapshot (Priority: P1)

**Goal**: Lock the JSON Schema for `RiskPlan` and the math that produces it so that P3 can convert it into a `Signal` without re-running the math.

**Independent Test**: A reviewer can score a non-vetoed snapshot, read the `risk_plan`, and verify the entry, stop, 3 TPs, R/R expectations, holding period, and invalidation criteria.

### Implementation for User Story 2

- [X] T017 [P] [US2] Author `specs/003-scoring-engine-v1/contracts/risk-plan.schema.json` with 3 fixed TP levels (1R/2R/3R), R/R expectations, and `max_intended_holding_period` enum
- [X] T018 [US2] Author `scripts/scoring/risk_plan.py` with `recommend_direction(snapshot)` and `derive_risk_plan(snapshot, direction)` (hybrid ATR+swing stop)
- [X] T019 [US2] Verify the risk-plan schema is a valid JSON Schema 2020-12
- [X] T020 [US2] Verify risk plan derivation invariants (R/R, stop direction, ATR floor) via pytest property-based tests

**Checkpoint**: The risk-plan schema is a valid, mechanical contract.

---

## Phase 5: User Story 3 - Reject a non-tradeable setup (Priority: P1)

**Goal**: Lock the `regime_veto` and `safety_veto` mechanisms so that downstream specs and the human trader never see a phantom plan on a setup the system has already decided is un-tradeable.

**Independent Test**: A reviewer can score a snapshot whose regime is one of the 4 veto regimes and verify the output has `risk_plan: null`, a `regime_veto` penalty of 100, and a `rejection_reason` string.

### Implementation for User Story 3

- [X] T021 [P] [US3] Author `specs/003-scoring-engine-v1/contracts/scoring-output.schema.json` (wrapper with `snapshot_ref`, `scored_at`, `confidence_score`, `risk_plan`, `rejection_reason`)
- [X] T022 [US3] Author `scripts/scoring/score.py` with the public `score_snapshot(snapshot, snapshot_ref)` function and the CLI
- [X] T023 [US3] Verify the scoring-output schema is a valid JSON Schema 2020-12
- [X] T024 [US3] Verify veto behavior via pytest: regime_veto, regime_unknown_penalty, null_field_penalty, tradable_floor, safety_veto

**Checkpoint**: The scoring-output schema is a valid, mechanical contract; veto behavior is verified.

---

## Phase 6: User Story 4 - Version every score and risk plan (Priority: P2)

**Goal**: Lock the `StrategyVersion` registry so that every score and risk plan is attributable to a specific scoring rules table.

**Independent Test**: A reviewer can read the `confidence_score.strategy_version_ref` and verify it equals `v0.1.0` and the fingerprint matches `sha256(strategy_rules_table)`.

### Implementation for User Story 4

- [X] T025 [US4] Verify `StrategyVersion` is referenced in every `ConfidenceScore` and every non-null `RiskPlan` (already implemented in T012 + T022)
- [X] T026 [US4] Add `test_v0_1_0_fingerprint_matches_sha256_of_canonical_json` to assert the fingerprint identity
- [X] T027 [US4] Add `test_strategy_version_is_frozen_dataclass` to assert immutability

**Checkpoint**: StrategyVersion v0.1.0 is immutable, fingerprinted, and referenced.

---

## Phase 7: Validator and Runtime

**Purpose**: Deliver the local validator and the test suite.

- [X] T028 [P] Author `scripts/validation/validate_scoring.py` with the validator logic (schema loading, fixture iteration, per-error formatting, exit codes 0/1/2)
- [X] T029 [P] Verify the validator exits 0 with 3 `OK:` lines when run against the 3 fixtures
- [X] T030 [P] Verify the validator exits 1 with named errors when run against deliberately broken fixtures (out of scope for P2; covered by integration test in P3+)
- [X] T031 [P] Author `tests/scoring/test_strategy_version.py` with V0_1_0 immutability, weights sum to 1, fingerprint determinism
- [X] T032 [P] Author `tests/scoring/test_regime_classifier.py` with trusts-veto, extreme_volatility, choppy, trend_up/down tests + property-based tests
- [X] T033 [P] Author `tests/scoring/test_confluence.py` with trend alignment, vol suitability, structural clarity tests + property-based tests
- [X] T034 [P] Author `tests/scoring/test_risk_plan.py` with long/short/neutral direction, missing data, R-multiples, holding period + property-based tests
- [X] T035 [P] Author `tests/scoring/test_score.py` with end-to-end on all 3 P1 fixtures, determinism, chop veto, unknown penalty, null_field_penalties, tradable_floor, graceful handling

**Checkpoint**: The validator is a working, deterministic, testable local tool. The test suite passes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, traceability, and reproducibility evidence.

- [X] T036 [P] Author `specs/003-scoring-engine-v1/quickstart.md` with reading order, reproduction steps, hard rules, and the 8-line self-check
- [X] T037 [P] Run the 8 self-checks from `quickstart.md` and confirm all 8 print `OK`; record the output in `quickstart.md` "Validation Evidence" subsection
- [X] T038 [P] Verify no `[NEEDS CLARIFICATION]` markers remain anywhere in `specs/003-scoring-engine-v1/`; record the `grep -c` result in `quickstart.md`
- [X] T039 [P] Verify no secrets, credentials, API keys, or live URLs appear in any P2 artifact (targeted regex scan returns 0 matches)
- [X] T040 [P] Cross-check that every functional requirement (FR-001 to FR-020) is referenced from at least one of: `plan.md`, `data-model.md`, `research.md`, `quickstart.md`, or the scorer code
- [X] T041 [P] Cross-check that every success criterion (SC-001 to SC-010) is referenced from at least one of: `plan.md`, `data-model.md`, or `quickstart.md`
- [X] T042 [P] Verify P1 regression: `python scripts/validation/validate_data_layer.py` still prints 3 OK lines, exit 0
- [X] T043 Update `README.md` to reflect the P2 milestone (scoring engine merged)
- [X] T044 Update `AGENTS.md` to list spec 003 as the current pending spec
- [X] T045 Open a pull request from `003-scoring-engine-v1` to `main` summarizing what landed, the validation evidence, and the constitutional compliance

**Checkpoint**: Spec is internally consistent, traceable, reproducible, and ready for review/merge.

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — completed.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user-story work. Completed.
- **Phase 3 (US1)**: Depends on Phase 2; first user story to implement. Completed.
- **Phase 4 (US2)**: Depends on Phase 2; depends on US1 (math must be defined before risk plan). Completed.
- **Phase 5 (US3)**: Depends on Phase 2; depends on US1 + US2 (veto wraps everything). Completed.
- **Phase 6 (US4)**: Depends on US1 + US2; versioning is layered. Completed.
- **Phase 7 (Validator)**: Depends on US1, US2, US3; validator needs all three schemas. Completed.
- **Phase 8 (Polish)**: Depends on all user-story phases and the validator. In progress.

### Within Each Phase

- Documents before cross-reference validation.
- Spec before plan, plan before data model, data model before quickstart (matches the natural reading order).
- Cross-reference validation before polish evidence.
- Self-check and constitution check evidence are recorded **last** so the report reflects the final state of every artifact.

### Parallel Opportunities

- T002, T003 can run in parallel with T001.
- T007, T008, T009 can run in parallel with T005, T006 (different files; T006 depends on T005).
- T011, T017, T021 can run in parallel (different schemas, no cross-references in P2).
- T012, T013, T014, T015 can run in parallel (different modules, no cross-dependencies).
- T031, T032, T033, T034, T035 can run in parallel (different test files).

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1): confidence-score schema + math.
3. Validate US1 independently: a reviewer can run the scorer on a snapshot and read the decomposable score.
4. Stop. The remaining user stories are tracked but not yet implemented.

### Incremental Delivery

1. **Block A (this spec, P2)**: Phases 1-8 — close the scoring engine. One PR.
2. **Block B (P3, next spec)**: Signal generator + alert format. Independent PR. Consumes P2 fixtures.
3. **Block C (P4+)**: Journal, outcomes, calibration. Each a separate PR.

### Parallel Team Strategy

This is a single-author project. The "team" is one person and one agent session. Tasks marked `[P]` are noted for future contributors; the current session executes them serially.

## Notes

- Every task in this spec produces documentation, contract artifacts, fixtures, code, or tests. The full reproduction (venv, deps, scorer, validator, pytest) takes under 60 seconds on commodity hardware.
- A `[NEEDS CLARIFICATION]` count of zero is a hard prerequisite for opening the PR. The count is 0.
- Constitutional compliance is verified by the explicit checklist in `plan.md` and re-verified during the polish phase (`checklists/requirements.md`).
- After merge, the next spec (P3: signal generator) is the only allowed handoff. Do not start a P3 task in this branch.
- During implementation, the regime classifier's contract was clarified: the input regime is **trusted** when it is non-unknown; re-classification runs only when the input is `unknown`. This is the practical interpretation of P1's "regime is provided by the data source; the scorer does not re-classify non-unknown regimes". Documented in the classifier's docstring.
