# crypto-alpha

> Personal, industrial-grade AI-assisted crypto futures trading intelligence.
> This repository hosts the project; the canonical project name is **crypto-alpha**.

## Purpose

crypto-alpha exists to improve the quality of personal crypto futures trading decisions. It is not a signal-spam bot. Every feature is evaluated against its contribution to risk-adjusted profitability, trade quality, selectivity, and loss containment.

The system observes the market, detects structured setups, evaluates confluence, calculates risk plans, emits alerts, tracks real manual trades, and feeds outcomes back into the model — all under a strict governance loop that distinguishes **what the system recommended** from **what the trader actually did**.

## Scope (current phase)

This repository is in the **specification foundation** phase. No runtime code is implemented yet. Work is limited to:

- Constitution, specs, plans, and tasks under `.specify/`.
- The first feature: `specs/001-profitable-trading-decision-domain/` — the foundational product domain that defines the entities (Trading Universe, Watchlist Asset, Opportunity, Signal, Risk Plan, Confidence Score, Manual Trade Record, Trade Outcome, Learning Observation, Execution Intent, Strategy Version).
- Lightweight local validation scripts when a future spec authorizes them.

## Non-Goals (this phase)

- No data ingestion logic.
- No exchange connectors or live API calls.
- No order placement, manual or automated.
- No AI analysis, RAG, autonomous agents, or prompt orchestration.
- No dashboard, FastAPI, database, Kafka, AWS, or cloud automation.
- No trading signals, recommendations, ratings, target prices, or forecasts.

## Disclaimer

This project is for **educational and personal trading intelligence purposes only**. It does not provide investment advice, portfolio allocation guidance, or buy/sell/hold recommendations. Any output from the system, once implemented, MUST include a non-advice disclaimer.

Crypto futures and perpetual futures involve substantial risk and may not be suitable for all investors.

## Methodology

crypto-alpha is governed by **Spec-Driven Development (SDD) using Spec Kit**. Every iteration follows the same loop:

1. **Specify** the scope, constraints, and acceptance criteria in `specs/NNN-…/spec.md`.
2. **Clarify** ambiguities before planning when they affect trading behavior, risk, data semantics, learning, or future execution.
3. **Plan** the architecture, contracts, tests, operational risks, and observability in `specs/NNN-…/plan.md`.
4. **Task** the work into independently testable increments in `specs/NNN-…/tasks.md`.
5. **Implement** against tasks; run validation; capture evidence.
6. **Review** via pull request; merge only after acceptance criteria are met and validation evidence is documented.

Code serves the specification, never the reverse. No material capability may be implemented without a corresponding spec, acceptance criteria, and validation path.

## Repository Layout

```text
.
├── .specify/                   # Spec Kit governance (constitution, templates, workflows, commands)
│   └── memory/constitution.md  # Project constitution (v1.0.0)
├── specs/                      # All feature specs live here
│   ├── 001-profitable-trading-decision-domain/  # Merged (PR #1)
│   └── 002-data-layer/         # Merged (PR #3)
│       ├── spec.md             # Feature specification
│       ├── plan.md
│       ├── research.md
│       ├── data-model.md
│       ├── quickstart.md
│       ├── tasks.md
│       ├── checklists/
│       ├── contracts/          # JSON Schemas
│       └── fixtures/           # Deterministic sample data
├── scripts/
│   └── validation/             # Local validators
├── pyproject.toml              # Python project metadata (jsonschema dep)
├── AGENTS.md                   # Agent operating instructions
└── README.md                   # This file
```

## Constitutional Principles

The full constitution lives in [`.specify/memory/constitution.md`](.specify/memory/constitution.md). The seven core principles are:

1. **Risk-Adjusted Profitability Over Signal Volume** — selectivity, expectancy, and drawdown matter more than alert count.
2. **Spec-Driven, Iteration-Bounded Delivery** — every iteration maps to a small spec; code serves the spec.
3. **Futures-First, Multi-Asset Opportunity Intelligence** — dynamic watchlist; no BTC-only assumptions.
4. **Traceable Decisions and Auditable Intelligence** — every signal, trade, and adjustment must be explainable from stored evidence.
5. **Manual-First Execution, Automation-Compatible Architecture** — alerts + manual journal from day one; automation is a future, separately spec'd capability.
6. **Learning Requires Evidence, Versioning, and Guardrails** — controlled feedback loop, never silent mutation.
7. **Industrial Maintainability for Personal Use** — modular, testable, observable, secure, reproducible.

## Current Status

| Area | Status |
|---|---|
| Constitution v1.0.0 | Ratified 2026-06-15 |
| Spec 001 `profitable-trading-decision-domain` | Merged (PR #1) |
| Spec 002 `data-layer` | Merged (PR #3) |
| Runtime code | Validator + 3 JSON Schemas + 3 fixtures shipped in spec 002 |
| CI / validation scripts | Local validator only (no CI yet) |
| Remote | `https://github.com/SergioRmz/crypto-alpha.git` |

## Working With This Repository

- Read `.specify/memory/constitution.md` first.
- Read `AGENTS.md` for agent operating instructions.
- Spec work goes under `specs/NNN-short-name/` following the templates in `.specify/templates/`.
- Specs, plans, tasks, and implementation MUST be done in a feature branch, committed in coherent blocks, and merged through a pull request.
- For data layer validation (spec 002), use the local validator:
  ```bash
  uv venv --python 3.11 .venv && source .venv/bin/activate && uv pip install -e .
  python scripts/validation/validate_data_layer.py
  ```
  Expected: 3 `OK:` lines, exit 0.

## Future Stack (planned, not implemented)

- Backend APIs and data workflows: Python with FastAPI.
- Dashboard: Next.js.
- Event streaming: Kafka, only after deterministic ingestion baselines are validated.
- Cloud: low-cost AWS serverless, only when usage justifies it.

These targets are documented in the constitution to constrain future specs, not to authorize premature implementation. Each of them requires its own dedicated spec with acceptance criteria before any code is written.

---

**crypto-alpha** — A disciplined, evidence-backed, spec-driven approach to personal crypto futures trading intelligence.
