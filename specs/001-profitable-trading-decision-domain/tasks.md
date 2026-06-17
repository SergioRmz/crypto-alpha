# Tasks: Profitable Trading Decision Domain

**Input**: Design documents from `specs/001-profitable-trading-decision-domain/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md` (all present)
**Tests**: Validation tasks are included because this feature is contract-first, scope-critical, and must be reproducible from a clean clone.
**Organization**: Tasks are grouped by user story to enable independent verification. This is a **documentation/conceptual** spec, so "implementation" tasks here produce documentation, contracts, and validation artifacts — not runtime code. Runtime code is intentionally deferred to P1+ in `plan.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the documentation directory structure for this spec, ensure Spec Kit artifacts are aligned with the project.

- [X] T001 Create `specs/001-profitable-trading-decision-domain/` directory and `checklists/` subdirectory
- [X] T002 [P] Verify `.specify/memory/constitution.md` v1.0.0 is present and referenced from `README.md` and `AGENTS.md`
- [X] T003 [P] Verify `.specify/templates/` contains `spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`, `constitution-template.md`
- [X] T004 [P] Verify `.specify/commands/` includes `speckit.specify`, `speckit.clarify`, `speckit.plan`, `speckit.tasks`, `speckit.checklist` command definitions

**Checkpoint**: Documentation scaffolding is ready; spec authors can write the foundation documents.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the foundational documents (spec, plan, research, data model, quickstart) and the constitution check before any user-story work.

**⚠️ CRITICAL**: No user-story work can begin until this phase is complete.

- [X] T005 Author `specs/001-profitable-trading-decision-domain/spec.md` with 4 user stories, 18 functional requirements, 12 key entities, 8 success criteria, and the assumptions block (per `.specify/templates/spec-template.md`)
- [X] T006 Author `specs/001-profitable-trading-decision-domain/checklists/requirements.md` confirming content quality, requirement completeness, and feature readiness, with no `[NEEDS CLARIFICATION]` markers remaining
- [X] T007 [P] Author `specs/001-profitable-trading-decision-domain/research.md` capturing design precedents, why-this-shape reasoning, and the open research questions deferred to later specs
- [X] T008 [P] Author `specs/001-profitable-trading-decision-domain/data-model.md` with the full entity graph, invariants, cardinality summary, lifecycle states, and field conventions
- [X] T009 [P] Author `specs/001-profitable-trading-decision-domain/quickstart.md` with reading order, application rules, hard rules, and self-check shell snippets
- [X] T010 Author `specs/001-profitable-trading-decision-domain/plan.md` with summary, technical context, constitution check, project structure, and the P0–P7+ domain phasing roadmap
- [X] T011 [P] Author `README.md` at repository root serving as the project entry point, linking the constitution, AGENTS, and the spec roadmap
- [X] T012 Run the constitution check in `plan.md` against `.specify/memory/constitution.md`; confirm all seven principles are addressed; document the result in `quickstart.md`
- [X] T013 Run the self-check shell snippets from `quickstart.md` and confirm all five `OK` lines print

**Checkpoint**: All foundational documents exist, the constitution check passes, and the self-check confirms internal consistency.

---

## Phase 3: User Story 1 - Evaluate high-quality trading opportunities (Priority: P1)

**Goal**: Lock the domain semantics that distinguish a high-quality opportunity from noise, so all later specs can use the same vocabulary.

**Independent Test**: A reviewer can read the spec, plan, data model, and Q1 clarification and answer: "What makes an opportunity tradable in v1, and what happens when it isn't?" with a precise, evidence-backed answer.

### Validation for User Story 1

- [X] T014 [P] [US1] Verify that `spec.md` US1 acceptance scenarios map to FR-003, FR-005, FR-009, FR-012, FR-015 and to SC-001/SC-005; record the cross-reference table in `quickstart.md` "How to apply the spec" section
- [X] T015 [P] [US1] Verify the Q1 clarification (high-quality opportunity gates: invalidation, R/R ≥ 1.5, structural evidence, no veto) is referenced from `data-model.md` "Invariants" section
- [X] T016 [US1] Add a "US1 cross-reference" subsection to `quickstart.md` listing the entity fields, invariants, and lifecycle states that implement US1

**Checkpoint**: US1 is traceable from spec → FR → SC → data model → quickstart without ambiguity.

---

## Phase 4: User Story 2 - Separate signal recommendation from real manual trade execution (Priority: P1)

**Goal**: Lock the relationship between `Signal`, `ManualTradeRecord`, and `TradeOutcome` so execution deviations are captured and learning is not corrupted.

**Independent Test**: A reviewer can read the spec, Q2 clarification, and data model and explain in 60 seconds: (a) the three link modes between signal and manual trade; (b) how theoretical and actual results are stored separately; (c) which fields are required vs optional in the v1 journal.

### Validation for User Story 2

- [X] T017 [P] [US2] Verify Q2 clarification (signal vs manual separation, link modes, theoretical vs actual result split) is referenced from `data-model.md` "Invariants" (Invariants 2 and 3) and from the `TradeOutcome` entity description
- [X] T018 [P] [US2] Verify that the v1 journal minimum fields from Q3 (`id`, `instrument`, `direction`, `entry_price`, `entry_timestamp`, `stop_loss`, `take_profit_plan[]`, `risk_per_unit`, `size_or_normalized_exposure`, `fees_paid`, `regime`, `strategy_version`, `notes`, plus the outcome fields) are listed in `data-model.md` "Field conventions" or under the relevant entity descriptions
- [X] T019 [US2] Add a "US2 cross-reference" subsection to `quickstart.md` listing the link modes, the `TradeOutcome.theoretical_signal_result` vs `actual_manual_result` split, and the journal minimum field set

**Checkpoint**: US2 is traceable; the journal minimum is explicit; theoretical vs actual separation is unambiguous.

---

## Phase 5: User Story 3 - Track outcome quality for learning (Priority: P1)

**Goal**: Lock the outcome model and the quality label taxonomy so future learning specs can use it without re-opening the foundation.

**Independent Test**: A reviewer can list the seven quality label categories, explain what a `LearningObservation` is allowed to do in v1 (record only, not mutate), and point to the spec clauses that enforce this.

### Validation for User Story 3

- [X] T020 [P] [US3] Verify that SC-006 (every outcome carries at least one quality label) and the seven label categories (thesis, timing, entry, stop, target, execution, regime) are referenced in `data-model.md` under the `TradeOutcome` entity
- [X] T021 [P] [US3] Verify FR-013 (learning observations reference evidence, do not mutate strategy behavior) is reflected in `plan.md` "Risk and Guardrails" as a hard rule
- [X] T022 [US3] Add a "US3 cross-reference" subsection to `quickstart.md` listing the quality label categories, the `LearningObservation` read-only contract, and the path to P6 (confidence calibration) as the first spec that may relax the read-only rule

**Checkpoint**: US3 is traceable; the read-only contract on `LearningObservation` is explicit; the path to learning is documented.

---

## Phase 6: User Story 4 - Preserve future execution compatibility without enabling automation (Priority: P2)

**Goal**: Lock the `ExecutionIntent` entity as future-compatibility scaffolding without enabling any automated order placement.

**Independent Test**: A reviewer can confirm that no spec, plan, or task in this feature wires `ExecutionIntent` to an order placement adapter, and that the constitution's "no automated execution" rule is mirrored in the plan's hard rules.

### Validation for User Story 4

- [X] T023 [P] [US4] Verify FR-016 (`ExecutionIntent` exists for future-compatibility; this spec does not authorize automation) is reflected in `data-model.md` `ExecutionIntent` entity description and in `plan.md` "Risk and Guardrails" as a hard rule
- [X] T024 [P] [US4] Verify that no task in this `tasks.md` introduces a runtime code path, exchange adapter, FastAPI endpoint, or order placement helper
- [X] T025 [US4] Add a "US4 cross-reference" subsection to `quickstart.md` listing the `ExecutionIntent` fields, the read-only contract in v1, and the requirement for a dedicated execution-safety spec before any future spec may wire it

**Checkpoint**: US4 is traceable; the "no automation" invariant is documented; the path to a future execution spec is preserved.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, traceability, and reproducibility evidence.

- [X] T026 [P] Cross-check that every functional requirement (FR-001 to FR-018) is referenced from at least one of: `plan.md`, `data-model.md`, `research.md`, or `quickstart.md`; record the mapping in `quickstart.md` "FR coverage" subsection
- [X] T027 [P] Cross-check that every success criterion (SC-001 to SC-008) is referenced from at least one of: `plan.md`, `data-model.md`, or `quickstart.md`; record the mapping in `quickstart.md` "SC coverage" subsection
- [X] T028 [P] Confirm `AGENTS.md` is consistent with the new `README.md` (no contradictory instructions, no missing links to constitution or spec roadmap)
- [X] T029 [P] Run the self-check from `quickstart.md` and confirm 5/5 `OK` lines print; record the output in `quickstart.md` "Validation evidence" subsection
- [X] T030 Verify no `[NEEDS CLARIFICATION]` markers remain anywhere in `specs/001-profitable-trading-decision-domain/`; record the `grep -c` result in `quickstart.md` "Validation evidence" subsection
- [X] T031 Verify the constitution check in `plan.md` lists all seven principles as addressed; record the explicit list in `quickstart.md` "Validation evidence" subsection
- [X] T032 Open a pull request from `001-profitable-trading-decision-domain` to `main` summarizing what landed, the validation evidence, and the constitutional compliance

**Checkpoint**: Spec is internally consistent, traceable, reproducible, and ready for review/merge.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user-story validation.
- **Phase 3 (US1)**: Depends on Phase 2; first user story to verify.
- **Phase 4 (US2)**: Depends on Phase 2; benefits from US1 cross-references in place.
- **Phase 5 (US3)**: Depends on Phase 2; benefits from US1 and US2 cross-references.
- **Phase 6 (US4)**: Depends on Phase 2; can run in parallel with US1–US3 cross-reference work.
- **Phase 7 (Polish)**: Depends on all user-story phases being verified.

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational; no dependency on US2/US3/US4.
- **US2 (P1)**: Can start after Foundational; cross-references the journal minimum fields.
- **US3 (P1)**: Can start after Foundational; cross-references the outcome and learning model.
- **US4 (P2)**: Can start after Foundational; cross-references the execution safety contract.

### Within Each Phase

- Documents before cross-reference validation.
- Spec before plan, plan before data model, data model before quickstart (matches the natural reading order).
- Cross-reference validation before polish evidence.
- Self-check and constitution check evidence are recorded **last** so the report reflects the final state of every artifact.

### Parallel Opportunities

- T002, T003, T004 can run in parallel (different files).
- T007, T008, T009, T011 can run in parallel with T005/T006 (different files; T010 depends on T005/T006/T007/T008/T009).
- All user-story cross-reference tasks (T014–T025) can run in parallel because they touch different subsections of `quickstart.md` and `data-model.md` if the team is split.
- T026, T027, T028, T029, T030, T031 can run in parallel during polish.

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1) cross-reference validation.
3. Validate US1 independently: a reviewer can answer the tradability question in under five minutes using only the spec, data model, plan, and Q1 clarification.
4. Stop. The remaining user stories are tracked but not yet validated.

### Incremental Delivery

1. **Block A (this spec, P0)**: Phase 1 + Phase 2 + Phase 3 + Phase 4 + Phase 5 + Phase 6 + Phase 7 — close the conceptual foundation. One PR.
2. **Block B (P1, next spec)**: Data layer with sample fixtures, no live API. Independent PR.
3. **Block C (P2)**: Scoring engine v1. Independent PR.
4. **Block D (P3)**: Signal generator and alert format. Independent PR.
5. **Block E (P4–P6)**: Journal, outcomes, calibration. Each a separate PR.

### Parallel Team Strategy

This is a single-author project. The "team" is one person and one agent session. Tasks marked `[P]` are noted for future contributors; the current session executes them serially.

## Notes

- Every task in this spec produces documentation, contracts, or validation evidence. None produces runtime code. Runtime code is intentionally deferred to P1+.
- The five self-check shell snippets in `quickstart.md` are the only validation tooling required for this spec. A real CI script is deferred to a later spec.
- A `[NEEDS CLARIFICATION]` count of zero is a hard prerequisite for opening the PR. If the count is non-zero, the spec is not ready for review.
- Constitutional compliance is verified by the explicit checklist in `plan.md` and re-verified during the polish phase (`quickstart.md` "Validation evidence" subsection).
- After merge, the next spec (P1: data layer) is the only allowed handoff. Do not start a P1 task in this branch.
