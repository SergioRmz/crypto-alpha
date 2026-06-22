# Tasks: Data Layer (P1)

**Input**: Design documents from `specs/002-data-layer/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md` (all present)
**Tests**: Validation tasks are included because P1 is contract-first and the validator is the test surface.
**Organization**: Tasks are grouped by user story to enable independent verification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the documentation directory structure and runtime scaffolding for this spec.

- [X] T001 Create `specs/002-data-layer/` directory and `contracts/`, `fixtures/`, `checklists/` subdirectories
- [X] T002 [P] Add `.gitignore` for Python venv, editor files, OS artifacts
- [X] T003 [P] Create branch `002-data-layer` from `main` and verify clean working tree

**Checkpoint**: Documentation scaffolding is ready; spec authors can write the foundation documents.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the foundational documents (spec, plan, research, data model) and the constitution check before any user-story work.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [X] T004 Author `specs/002-data-layer/spec.md` with 3 user stories, 15 functional requirements, 5 key entities, 7 success criteria, 12 clarifications, and the assumptions block
- [X] T005 Author `specs/002-data-layer/plan.md` with summary, technical context, constitution check, project structure, and the P0→P1 handoff documentation
- [X] T006 [P] Author `specs/002-data-layer/research.md` capturing 12 design decisions (D1-D12), 3 precedent scans (CCXT, Tardis/Databento, Nautilus Trader), and 8 open research questions (R1-R8)
- [X] T007 [P] Author `specs/002-data-layer/data-model.md` with field-level precision for the 3 schemas (snapshot, watchlist-asset, trading-universe)
- [X] T008 [P] Author `specs/002-data-layer/checklists/requirements.md` confirming content quality, requirement completeness, feature readiness, and constitutional compliance
- [X] T009 Run the constitution check in `plan.md` against `spec-001/constitution.md`; confirm all seven principles are addressed; document the result in `plan.md`

**Checkpoint**: All foundational documents exist, the constitution check passes, and the spec is internally consistent.

---

## Phase 3: User Story 1 - Author and validate a market snapshot (Priority: P1)

**Goal**: Lock the JSON Schema for `MarketContextSnapshot` so that any snapshot is mechanically validated.

**Independent Test**: A reviewer can author a new snapshot JSON and run the validator; the validator either prints `OK:` for the file or names the offending field with a human-readable error.

### Implementation for User Story 1

- [X] T010 [P] [US1] Author `specs/002-data-layer/contracts/snapshot.schema.json` (JSON Schema 2020-12) with all required fields, the 6-timeframe keyed map, the strict 8-value regime enum, the required-but-nullable derivatives context, and the `disclaimer_present: const true` invariant
- [X] T011 [US1] Verify the snapshot schema is a valid JSON Schema 2020-12 (jsonschema's `Draft202012Validator.check_schema(schema)` must pass)
- [X] T012 [US1] Verify the snapshot schema rejects each of: missing required field, wrong type, invalid enum value, missing timeframe key, non-UTC timestamp, non-decimal-string money value

**Checkpoint**: The snapshot schema is a valid, mechanical contract.

---

## Phase 4: User Story 2 - Cover the watchlist with multi-asset fixtures (Priority: P1)

**Goal**: Ship three deterministic multi-asset fixtures (BTC, ETH, SOL perp) that pass the validator.

**Independent Test**: Running the validator against the three fixtures prints exactly 3 `OK:` lines and exits 0.

### Implementation for User Story 2

- [X] T013 [P] [US2] Author `specs/002-data-layer/fixtures/btc-perp-snapshot.json` with synthetic but plausible data, regime `trend_up`, and all 6 timeframes populated
- [X] T014 [P] [US2] Author `specs/002-data-layer/fixtures/eth-perp-snapshot.json` with regime `range` (distinct from BTC)
- [X] T015 [P] [US2] Author `specs/002-data-layer/fixtures/sol-perp-snapshot.json` with regime `extreme_volatility` (distinct from both) and higher vol/ATR numbers
- [X] T016 [US2] Verify the three fixtures span at least two distinct regime values (regression guard against copy-paste-with-find-replace)

**Checkpoint**: Three valid, multi-asset, multi-regime fixtures exist.

---

## Phase 5: User Story 3 - Define a watchlist and a trading universe (Priority: P2)

**Goal**: Lock the JSON Schemas for `WatchlistAsset` and `TradingUniverse` so that the system can express "which assets are eligible" without coupling to a specific venue.

**Independent Test**: Constructing a `TradingUniverse` JSON containing three `WatchlistAsset` entries and validating it against the schema succeeds.

### Implementation for User Story 3

- [X] T017 [P] [US3] Author `specs/002-data-layer/contracts/watchlist-asset.schema.json` with all required fields, the data_availability subobject, and the nullable `liquidity_suitability`
- [X] T018 [P] [US3] Author `specs/002-data-layer/contracts/trading-universe.schema.json` requiring a non-empty `assets[]` and referencing the watchlist-asset schema via `$ref`
- [X] T019 [US3] Verify the two schemas compose correctly (a `TradingUniverse` JSON validating against `trading-universe.schema.json` cascades validation to `watchlist-asset.schema.json` for each item in `assets`)

**Checkpoint**: The watchlist and universe schemas are valid, composable contracts.

---

## Phase 6: Validator and Runtime

**Purpose**: Deliver the local validator script that ties everything together.

- [X] T020 [P] Add `pyproject.toml` declaring `jsonschema>=4.0,<5.0` as the only external runtime dep, managed by `uv`
- [X] T021 Author `scripts/validation/validate_data_layer.py` with the validator logic: schema loading, fixture iteration, per-error formatting, exit codes (0/1/2)
- [X] T022 [P] Verify the validator exits 0 with 3 `OK:` lines when run against the three fixtures
- [X] T023 [P] Verify the validator exits 1 with named errors when run against deliberately broken fixtures (one missing field, one wrong enum, one missing timeframe key)
- [X] T024 [P] Verify the validator is deterministic: same inputs produce same output and exit code across runs

**Checkpoint**: The validator is a working, deterministic, testable local tool.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, traceability, and reproducibility evidence.

- [X] T025 [P] Author `specs/002-data-layer/quickstart.md` with reading order, reproduction steps, hard rules, and the 8-line self-check
- [X] T026 [P] Run the 8 self-checks from `quickstart.md` and confirm all 8 print `OK`; record the output in `quickstart.md` "Validation Evidence" subsection
- [X] T027 [P] Verify no `[NEEDS CLARIFICATION]` markers remain anywhere in `specs/002-data-layer/`; record the `grep -c` result in `quickstart.md`
- [X] T028 [P] Verify no secrets, credentials, API keys, or live URLs appear in any P1 artifact (`grep -RIn 'sk-\|api_key\|secret\|live\.' specs/002-data-layer/ scripts/validation/ pyproject.toml` returns 0 matches)
- [X] T029 [P] Cross-check that every functional requirement (FR-001 to FR-015) is referenced from at least one of: `plan.md`, `data-model.md`, `research.md`, `quickstart.md`, or the validator code
- [X] T030 [P] Cross-check that every success criterion (SC-001 to SC-007) is referenced from at least one of: `plan.md`, `data-model.md`, or `quickstart.md`
- [X] T031 Open a pull request from `002-data-layer` to `main` summarizing what landed, the validation evidence, and the constitutional compliance

**Checkpoint**: Spec is internally consistent, traceable, reproducible, and ready for review/merge.

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — completed.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user-story work. Completed.
- **Phase 3 (US1)**: Depends on Phase 2; first user story to implement. Completed.
- **Phase 4 (US2)**: Depends on Phase 2; depends on US1 (snapshots must be defined before fixtures can conform). Completed.
- **Phase 5 (US3)**: Depends on Phase 2; can run in parallel with US1 (different schemas, no cross-references in P1). Completed.
- **Phase 6 (Validator)**: Depends on US1, US2, US3 (validator needs all three schemas and the three fixtures). Completed.
- **Phase 7 (Polish)**: Depends on all user-story phases and the validator. In progress.

### Within Each Phase

- Documents before cross-reference validation.
- Spec before plan, plan before data model, data model before quickstart (matches the natural reading order).
- Cross-reference validation before polish evidence.
- Self-check and constitution check evidence are recorded **last** so the report reflects the final state of every artifact.

### Parallel Opportunities

- T002, T003 can run in parallel with T001.
- T006, T007, T008 can run in parallel with T004, T005 (different files; T005 depends on T004).
- T010, T017, T018 can run in parallel (different schemas, no cross-references in P1).
- T013, T014, T015 can run in parallel (different fixtures, all conform to the same snapshot schema).
- T020, T022, T023, T024 can run in parallel with T021 (different files; T022-T024 depend on T021).
- T025, T026, T027, T028, T029, T030 can run in parallel during polish.

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1): snapshot schema.
3. Validate US1 independently: a reviewer can author a snapshot and the validator either accepts it or names the violation.
4. Stop. The remaining user stories are tracked but not yet implemented.

### Incremental Delivery

1. **Block A (this spec, P1)**: Phases 1-7 — close the data layer. One PR.
2. **Block B (P2, next spec)**: Scoring engine v1. Independent PR. Consumes P1 fixtures.
3. **Block C (P3)**: Signal generator + alert format. Independent PR.
4. **Block D (P4+)**: Journal, outcomes, calibration. Each a separate PR.

### Parallel Team Strategy

This is a single-author project. The "team" is one person and one agent session. Tasks marked `[P]` are noted for future contributors; the current session executes them serially.

## Notes

- Every task in this spec produces documentation, contract artifacts, fixtures, or the validator script. None produces runtime scoring, ingestion, or execution code. Those are intentionally deferred to P2+.
- The 8 self-check shell snippets in `quickstart.md` are the only validation tooling required for this spec. A real `pytest` suite is deferred to a later spec.
- A `[NEEDS CLARIFICATION]` count of zero is a hard prerequisite for opening the PR. The count is 0.
- Constitutional compliance is verified by the explicit checklist in `plan.md` and re-verified during the polish phase (`checklists/requirements.md`).
- After merge, the next spec (P2: scoring engine) is the only allowed handoff. Do not start a P2 task in this branch.
