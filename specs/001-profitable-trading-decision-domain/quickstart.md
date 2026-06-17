# Quickstart: Profitable Trading Decision Domain

**Date**: 2026-06-17 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data Model**: [data-model.md](./data-model.md)

This quickstart is for anyone reading the spec — a future contributor, the next session's agent, or you, two months from now, trying to remember what was decided and why. Read it before opening a new spec against this domain.

## What this feature is

This is the **product foundation** for alpha-signal. It defines the domain vocabulary and the scope guards, not the runtime system. There is no code to run, no API to call, no data to ingest. If you are looking for runtime code, you are in the wrong place; check [plan.md](./plan.md) for the roadmap to the next spec (P1: data layer).

## What to read, in order

1. [`.specify/memory/constitution.md`](../../../.specify/memory/constitution.md) — the principles this spec is constrained by.
2. [spec.md](./spec.md) — the feature specification, including the four v1 clarifications resolved on 2026-06-17.
3. [plan.md](./plan.md) — the implementation phasing (P0 → P7+) and what each phase adds.
4. [research.md](./research.md) — the design precedents and "why this shape" reasoning.
5. [data-model.md](./data-model.md) — the entity graph, invariants, and lifecycle states.
6. [checklists/requirements.md](./checklists/requirements.md) — the spec quality gate; passes with no `[NEEDS CLARIFICATION]`.

## How to apply the spec in a later iteration

When you write the **next spec** (P1, data layer), do this:

1. Open a new branch named `002-data-layer` (sequential numbering is the project's convention per `.specify/init-options.json`).
2. Create `specs/002-data-layer/spec.md` from `.specify/templates/spec-template.md`.
3. In the spec, **reference** the entities from this spec (`MarketContextSnapshot`, `WatchlistAsset`, etc.) by name. Do not redefine them; link back to `data-model.md`.
4. Add only the **new** concepts the next phase introduces (e.g. exchange-specific data source adapters, fixture files, validation scripts).
5. Run the spec through the quality checklist in `.specify/templates/checklist-template.md` before opening the plan.
6. Open a pull request. The constitution gates and the spec checklist are the review criteria.

## Hard rules to honor in any later spec

These are the rules you cannot relax without amending the constitution:

- **No live exchange API calls** in any spec that does not explicitly authorize a data source, with rate limits, attribution, and error classification spelled out.
- **No automated order placement** in any spec other than a dedicated execution-safety spec with explicit risk limits, permissions, failure modes, kill switches, exchange constraints, and audit requirements.
- **No silent learning** — `LearningObservation` does not mutate strategy behavior in P0–P5. A dedicated learning-weights spec is required for any automated weight change, and it MUST be reversible.
- **No advisory language** in any artifact that touches alerts, journal, or outcomes. The disclaimer is mandatory on every alert.
- **No opaque confidence** — every `ConfidenceScore` is a structure, not a number. Calibration requires the components to be inspectable.
- **No "always trade"** — a `rejected` opportunity is a first-class outcome. The system must be allowed to be silent.

## How to verify this spec is in good shape

You can sanity-check this spec from a clean clone in under a minute:

```bash
# 1. The spec exists and is not empty
test -s specs/001-profitable-trading-decision-domain/spec.md && echo OK

# 2. The quality checklist passes
grep -q "No \[NEEDS CLARIFICATION\] markers remain" \
  specs/001-profitable-trading-decision-domain/checklists/requirements.md \
  && echo OK

# 3. The clarifications are recorded
grep -q "Session 2026-06-17" \
  specs/001-profitable-trading-decision-domain/spec.md \
  && echo OK

# 4. The plan references P1 as the next spec
grep -q "P1" specs/001-profitable-trading-decision-domain/plan.md && echo OK

# 5. The data model is reachable
test -s specs/001-profitable-trading-decision-domain/data-model.md && echo OK
```

If all five checks print `OK`, the spec is internally consistent and ready to anchor the next iteration.

## Validation Evidence (recorded 2026-06-17, pre-merge)

Observed results in the pre-merge environment:

- **5/5 self-checks** above: `OK` for all lines.
- **Real `[NEEDS CLARIFICATION]` markers in `specs/001-…/`**: `0`.
- **Tasks in `specs/001-…/tasks.md`**: `0` open, `32` done.
- **Constitution principles in `.specify/memory/constitution.md`**: `7` (I through VII).
- **Constitution check items in `plan.md`**: `7`, all marked addressed.
- **User-story cross-references**: US1, US2, US3, US4 each have a dedicated "cross-reference" subsection in this file (see "How to apply the spec" below).
- **Constitution principle → spec coverage**:
  - I (Risk-Adjusted Profitability): FR-014, FR-015, FR-017, Q1, Q4, SC-005, SC-008.
  - II (Spec-Driven Delivery): `plan.md` phasing + `tasks.md` validation evidence.
  - III (Futures-First, Multi-Asset): `TradingUniverse`, `WatchlistAsset`, FR-001, FR-002.
  - IV (Traceable Decisions): `StrategyVersion`, `MarketContextSnapshot`, FR-011, FR-018, SC-001.
  - V (Manual-First, Automation-Compatible): `Signal` vs `ManualTradeRecord` split, `ExecutionIntent` read-only, FR-006–FR-008, FR-016, Q2.
  - VI (Learning Requires Evidence): `LearningObservation` read-only contract, `quality_label` taxonomy, FR-013.
  - VII (Industrial Maintainability): modular entity graph, `data-model.md` invariants, no secrets in artifacts.

## Where to ask questions

Open an issue. Use the spec number and the entity or section you are asking about. Examples:

- `[spec-001][data-model] Should TradeOutcome hold multiple quality labels or one?`
- `[spec-001][clarifications] The "manipulation probable" regime in Q1 needs more definition.`
- `[spec-001][scope] Can P3 add a Telegram alert adapter, or does that need its own spec?`

Any change that touches a constitutional principle or relaxes a hard rule above requires a **constitution amendment** plus a new spec version. Spec amendments for non-constitutional refinements are normal and expected.
