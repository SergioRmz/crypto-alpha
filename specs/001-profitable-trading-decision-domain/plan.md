# Implementation Plan: Profitable Trading Decision Domain

**Branch**: `001-profitable-trading-decision-domain` | **Date**: 2026-06-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-profitable-trading-decision-domain/spec.md` (with clarifications resolved on 2026-06-17).

**Note**: This plan documents the conceptual architecture, domain contracts, and implementation phasing for the alpha-signal product foundation. It intentionally does not introduce runtime code or vendor choices; those land in later specs gated by this plan.

## Summary

Define the conceptual product domain for alpha-signal: a personal, AI-assisted crypto futures trading intelligence system that produces structured `Opportunity` candidates, confirms them into `Signal` alerts, separates them from `ManualTradeRecord` execution, captures `TradeOutcome` for learning, and feeds `LearningObservation` back into a versioned scoring loop. The plan locks the entity graph, the data contracts, the regime taxonomy, the quality gates, and the implementation phasing so future specs can build runtime data ingestion, scoring, alerts, and learning without re-opening foundational decisions.

## Technical Context

- **Language/Version**: Deferred. Constitution allows Python/FastAPI for APIs and data workflows; that choice is the recommendation, not a binding decision of this spec. The domain model is language-agnostic and will be expressed as JSON Schemas in later specs.
- **Primary Dependencies**: Deferred. No runtime dependencies introduced in this spec.
- **Storage**: Deferred to a later spec; recommended direction is append-only event log + derived projections, but not decided here.
- **Testing**: Test strategy will use a layered approach: contract tests against JSON Schemas, unit tests for scoring/confluence math, integration tests for snapshot-to-signal flow, regression tests for learning feedback. Tooling (pytest, jsonschema, etc.) is a later-spec decision.
- **Target Platform**: Developer workstation, Linux-first, container-friendly. No server, no cloud, no deployment in this spec.
- **Project Type**: Documentation/conceptual foundation. No runtime code in this feature.
- **Performance Goals**: Out of scope for the foundation; later specs will set latency targets for alert generation.
- **Constraints**:
  - No external APIs, scraping, or live exchange data in this feature.
  - No automated order placement of any kind, now or in any spec that builds on this one without a dedicated execution-safety spec.
  - Specs, plans, and tasks MUST be reproducible from a clean clone.
  - Secrets, credentials, and live market data MUST NOT be committed.
- **Scale/Scope**: Personal single-trader product. Multi-tenant, multi-user, billing, and permissions are explicitly out of scope per spec assumptions.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Risk-Adjusted Profitability Over Signal Volume (I)**: domain rejects opportunities failing any quality gate; "no-trade" is a first-class outcome (FR-015); profitability is anchored in R-multiples (FR-014, FR-017, Q4).
- [x] **Spec-Driven, Iteration-Bounded Delivery (II)**: this spec is one of the smallest possible iterations; no code, no vendor lock, no premature stack.
- [x] **Futures-First, Multi-Asset Opportunity Intelligence (III)**: `TradingUniverse` and `WatchlistAsset` model the dynamic universe; no BTC-only assumption.
- [x] **Traceable Decisions and Auditable Intelligence (IV)**: every entity carries versioned evidence; `StrategyVersion` and `MarketContextSnapshot` are first-class.
- [x] **Manual-First Execution, Automation-Compatible Architecture (V)**: `Signal` and `ManualTradeRecord` are separate entities; `ExecutionIntent` exists for future automation but is **read-only** in v1 (FR-016).
- [x] **Learning Requires Evidence, Versioning, and Guardrails (VI)**: `LearningObservation` references evidence and outcomes but **does not mutate strategy behavior** in this spec; mutation requires a later spec with weight-update rules and reversible configuration.
- [x] **Industrial Maintainability for Personal Use (VII)**: modular entities, versioned strategies, traceable contracts, secrets prohibited.

## Project Structure

### Documentation (this feature)

```text
specs/001-profitable-trading-decision-domain/
├── plan.md              # This file
├── research.md          # Phase 0: domain research & precedent scan
├── data-model.md        # Phase 1: entity graph, field reference, invariants
├── quickstart.md        # Phase 1: how to read and apply the spec
├── contracts/           # Phase 1: conceptual JSON Schema placeholders
│   ├── opportunity.schema.json
│   ├── signal.schema.json
│   ├── risk-plan.schema.json
│   ├── confidence-score.schema.json
│   ├── manual-trade-record.schema.json
│   ├── trade-outcome.schema.json
│   ├── learning-observation.schema.json
│   └── strategy-version.schema.json
├── checklists/
│   └── requirements.md
├── spec.md              # Spec (with clarifications)
└── tasks.md             # Phase 2: concrete implementation tasks
```

### Source Code (repository root)

```text
# No runtime code in this spec. The structure below is the target layout
# future specs will populate. Documented here to constrain future changes.
src/
├── alpha_signal/
│   ├── domain/             # Entities from data-model.md (later spec)
│   ├── scoring/            # Confluence math, regime classifier (later spec)
│   ├── alerts/             # Alert format & channels (later spec)
│   ├── journal/            # Signal/manual/outcome persistence (later spec)
│   └── learning/           # Versioned feedback loop (later spec)
tests/
├── contract/               # JSON Schema validation tests (later spec)
├── integration/            # End-to-end signal flow tests (later spec)
└── unit/                   # Domain and scoring unit tests (later spec)
scripts/
└── validation/             # Lightweight repo-local validators (later spec)
docs/
├── architecture/           # System layers & decision flow (later spec)
├── contracts/              # Human-readable contract docs (later spec)
├── policies/               # Allowed data sources, retention, etc. (later spec)
└── validation/             # Validation runbooks & checklists (later spec)
```

**Structure Decision**: Repository remains documentation-only in this spec. The target source tree is documented for future spec authors, not implemented. Adding files outside `specs/001-…/` requires a future spec.

## Domain Phasing

The implementation of alpha-signal is deliberately staggered into phases. Each phase produces its own spec, plan, tasks, and pull request, and is gated by the constitution and this spec.

| Phase | Spec focus | Adds | Consumes |
|---|---|---|---|
| **P0 (this spec, 001)** | Foundational product domain | Entity vocabulary, quality gates, journal minimum, profitability unit, scope guards | Constitution v1.0.0 |
| **P1 (next spec)** | Data Layer: market snapshot contract + sample fixtures (no live API) | `MarketContextSnapshot` schema, sample fixtures for BTC/ETH perps, local validation script | 001 entities |
| **P2** | Scoring Engine v1: confluence math + regime classifier | `ConfidenceScore` math, `Regime` classifier, unit tests, no live data | 001, P1 |
| **P3** | Signal Generator + Alert format | `Signal` entity, alert template (Telegram-ready), `RiskPlan` derivation | 001, P1, P2 |
| **P4** | Manual Trade Journal | `ManualTradeRecord` persistence, link/unlink to `Signal`, outcome reconciliation | 001, P3 |
| **P5** | Outcome Capture + Quality Labels | `TradeOutcome` capture, `quality_label` taxonomy, `LearningObservation` generation | 001, P4 |
| **P6** | Confidence Calibration | Calibration reports, drift detection, versioned weight adjustments | 001, P5 |
| **P7+ (deferred)** | Dashboard, multiple venues, supervised/automated execution | Each gated by its own dedicated spec with safety controls | 001 + earlier phases |

**Execution placement**: P1 may be opened as the next spec only after this spec (001) is merged. P0 → P1 is the only allowed handoff at this time.

## Risk and Guardrails (carried into later specs)

- **No live data without a dedicated data-source spec.** Any later spec that wants to call an exchange API MUST specify rate limits, attribution, error classification, and credentials handling before code is written.
- **No automated execution without an execution-safety spec.** `ExecutionIntent` exists for future-compatibility only; it MUST NOT be wired to an order placement adapter in any spec other than a dedicated execution spec.
- **No silent learning.** `LearningObservation` records suggested adjustments; it does not mutate weights, thresholds, or rules. A dedicated learning-weights spec is required for any automated change to scoring.
- **No opaque confidence.** `ConfidenceScore` is decomposable. Any spec that changes a component MUST record the change with a `StrategyVersion` reference.
- **No advisory language in artifacts.** All signal, journal, and outcome records MUST avoid buy/sell/hold, target prices, ratings, recommendations, or forecasts in compliance with the constitution and the project disclaimer.

## Complexity Tracking

No constitution violations or complexity exceptions are required for this feature.
