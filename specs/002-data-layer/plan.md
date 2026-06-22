# Implementation Plan: Data Layer

**Branch**: `002-data-layer` | **Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-data-layer/spec.md` (with 12 clarifications resolved in-session on 2026-06-21).

**Note**: This plan documents the data layer for crypto-alpha. It is the first spec to introduce runtime artifacts (a Python validator script), but it does NOT introduce data ingestion, scoring, persistence, or any exchange API. All data is synthetic fixtures; all validation is local and deterministic.

## Summary

Deliver the first runtime artifact of crypto-alpha: a **contract-first data layer** that the next phase (P2: scoring engine) can develop and test against without depending on a live exchange. The data layer produces three JSON Schemas (for `MarketContextSnapshot`, `WatchlistAsset`, `TradingUniverse`), three deterministic multi-asset fixtures (BTC, ETH, SOL perpetuals), and a local Python validator that enforces schema conformance. The validator uses `jsonschema` 4.x as its only external dependency and produces byte-identical output for the same inputs.

## Technical Context

- **Language/Version**: Python 3.11+ (confirmed in spec clarification C12).
- **Primary Dependencies**: `jsonschema` 4.x (only external runtime dep). Managed via `uv`.
- **Storage**: None. P1 is contract + fixtures only. No database, no JSON store, no file-based state beyond the fixtures themselves.
- **Testing**: Validator script is the primary test surface. P1 does not introduce a `pytest` suite yet; a future spec (P2 or later) will add unit tests using the deliberate-violation fixtures referenced in SC-002.
- **Target Platform**: Developer workstation, Linux-first. No server, no cloud, no deployment.
- **Project Type**: Contract-first data layer + local validation tool.
- **Performance Goals**: Validator completes the three-fixture check in under 1 second on commodity hardware. The 30-second end-to-end budget in SC-005 is dominated by venv creation and dependency install, which are one-time costs.
- **Constraints**:
  - No external network access required (and no live data allowed).
  - No secrets, no credentials, no live URLs in any P1 artifact.
  - Validation output is deterministic and byte-identical across runs.
  - Python 3.11+ only (to align with the perf and typing improvements).
  - Single external dependency: `jsonschema`. No `pydantic`, no `marshmallow`, no `attrs`.
- **Scale/Scope**: Three schemas, three fixtures, one validator script. Total artifact size under 100 KB.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Risk-Adjusted Profitability Over Signal Volume (I)**: P1 does not produce signals. The data layer enables P2 to be selective, not chatty. No regression risk on this principle.
- [x] **Spec-Driven, Iteration-Bounded Delivery (II)**: This spec is one of the smallest possible iterations that unblocks P2. Scope is locked.
- [x] **Futures-First, Multi-Asset Opportunity Intelligence (III)**: Schemas include `venue`, `instrument_type`, and `asset_class` as required fields. The `canonical_symbol` convention (C7) supports cross-venue disambiguation. Fixtures deliberately include three assets (BTC, ETH, SOL) at different market-cap tiers, preventing the data layer from being BTC-tilted.
- [x] **Traceable Decisions and Auditable Intelligence (IV)**: `MarketContextSnapshot.evidence_refs[]` is a required field (inherited from P0 `data-model.md`). Fixtures are deterministic and serve as test evidence for P2.
- [x] **Manual-First Execution, Automation-Compatible Architecture (V)**: P1 does not touch execution. The `ExecutionIntent` entity from P0 remains read-only in this spec.
- [x] **Learning Requires Evidence, Versioning, and Guardrails (VI)**: Snapshots carry `schema_version` and `captured_at`. The validator can later be wired to detect schema-version drift (future spec).
- [x] **Industrial Maintainability for Personal Use (VII)**: Schemas are versioned (`schema_version`). Dependencies are minimal and pinned via `uv`. Validation is reproducible. No secrets, no live data.

**No constitution violations, no complexity exceptions required.**

## Project Structure

### Documentation (this feature)

```text
specs/002-data-layer/
├── spec.md                # Feature specification (with 12 clarifications)
├── plan.md                # This file
├── research.md            # Phase 0: design decisions and precedent scan
├── data-model.md          # Phase 1: field-level precision for the 3 schemas
├── quickstart.md          # Phase 1: how to reproduce validation from a clean clone
├── checklists/
│   └── requirements.md    # Spec quality gate
├── contracts/             # Phase 1: JSON Schemas
│   ├── snapshot.schema.json
│   ├── watchlist-asset.schema.json
│   └── trading-universe.schema.json
└── fixtures/              # Phase 1: deterministic sample data
    ├── btc-perp-snapshot.json
    ├── eth-perp-snapshot.json
    └── sol-perp-snapshot.json
```

### Source Code (repository root)

```text
scripts/
└── validation/
    └── validate_data_layer.py   # Python validator: schema + fixtures
```

The validator takes a list of JSON files and validates each against the schema inferred from its filename (or accepts explicit `--schema file=schema` mappings). On success it prints one `OK` line per file. On failure it prints the file path, the JSON-pointer of the offending field, and a human-readable error, then exits non-zero.

**Structure Decision**: Single script under `scripts/validation/`. No package structure yet (no `__init__.py`, no `pyproject.toml` package) because there is exactly one runnable artifact. A `pyproject.toml` is added in this spec solely to declare the `jsonschema` dependency for `uv` reproducibility; it does not introduce a package layout.

### Auxiliary (this feature)

```text
pyproject.toml             # Declares project metadata + jsonschema dep (uv-managed)
.gitignore                 # Python venv, editor files (already added in scaffold commit)
```

## Domain Phasing

P1 is the smallest possible runtime handoff. It does not produce a running system; it produces **the contract that the next running system will consume**. The phasing within P1 is:

| Step | Output | Depends on |
|---|---|---|
| 1. Research | `research.md` | spec.md |
| 2. Data model | `data-model.md` | research.md |
| 3. Schemas | 3 `*.schema.json` files | data-model.md |
| 4. Fixtures | 3 `*-snapshot.json` files | schemas |
| 5. Validator | `scripts/validation/validate_data_layer.py` | schemas + fixtures |
| 6. Quickstart | `quickstart.md` | all of the above |
| 7. Quality gate | `checklists/requirements.md` | spec.md + plan.md |
| 8. Self-check | run validator + FR/SC coverage grep | all artifacts |

After P1, the next spec (P2: scoring engine) will:
- Consume these fixtures as test inputs.
- Reference the `MarketContextSnapshot` schema as the contract for any scoring output that includes a snapshot.
- NOT modify any P1 artifact without an amendment.

## Risk and Guardrails (carried into later specs)

- **No live data, ever in P1.** The validator runs offline. No network, no DNS, no file system outside the project tree.
- **No schema drift without versioning.** Any future change to a `*.schema.json` MUST bump `schema_version` in every fixture that conforms to it.
- **No advisory language.** The validator does not parse free text, so the spec-level guardrail (Constitution I) is satisfied by the absence of advisory fields in the snapshot schema. The journal field guardrail (FR-012) is P4–P5's responsibility; P1 only encodes the snapshot side.
- **No `liquidity_suitability` mutation.** P1 fixtures set this field to `null` (FR-014). P2 (scoring engine) is the documented owner.
- **No `cadence_seconds` in P1.** P3 owns cadence.
- **No external runtime deps beyond `jsonschema`.** If a future spec needs more, it MUST justify the addition in its own `plan.md` and bump this constraint explicitly.

## Complexity Tracking

No constitution violations, no complexity exceptions. The data layer is intentionally minimal: three schemas, three fixtures, one validator script, one project metadata file. Total addition to the repo: ~100 KB.

## Validation Evidence Targets (to be recorded in `quickstart.md`)

- `uv` venv creation time
- `jsonschema` install time
- Validator run time (3 fixtures, 3 schemas)
- `OK` line count
- Exit code
- `grep` for secrets: 0 matches
- `grep` for `[NEEDS CLARIFICATION]` in this spec: 0 matches
