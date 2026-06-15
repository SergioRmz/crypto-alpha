# alpha-signal Constitution

## Core Principles

### I. Risk-Adjusted Profitability Over Signal Volume
alpha-signal exists to improve personal crypto futures trading decisions, not to maximize the number of alerts. Every feature MUST be evaluated by its contribution to risk-adjusted profitability, trade quality, selectivity, and loss containment. A valid system outcome includes choosing not to trade. Win rate alone is insufficient; decisions MUST be measured with expectancy, average R, profit factor, drawdown, fees, slippage, execution quality, and capital efficiency where applicable.

### II. Spec-Driven, Iteration-Bounded Delivery
The project MUST be governed through Spec-Driven Development using Spec Kit. Each iteration SHOULD map to a small, well-defined spec that can move through clarification, plan, tasks, implementation, and verification. Code serves the specification, not the reverse. No material capability may be implemented without a corresponding spec, acceptance criteria, and validation path. Specs MUST distinguish scope, non-scope, assumptions, risks, and measurable success criteria.

### III. Futures-First, Multi-Asset Opportunity Intelligence
alpha-signal is designed for crypto futures and perpetual futures across a dynamic multi-asset watchlist, including major assets and altcoins when liquidity, risk, and signal quality justify inclusion. The system MUST model derivatives-specific context such as leverage, funding, open interest, liquidations, mark price vs last price, contract constraints, fees, slippage, and liquidation risk as the product matures. The system MUST optimize for high-quality opportunities over fixed-symbol monitoring; BTC-only assumptions are prohibited unless explicitly scoped for a temporary test fixture.

### IV. Traceable Decisions and Auditable Intelligence
Every signal, trade decision, confidence score, risk plan, and learning adjustment MUST be explainable from stored evidence. The system MUST preserve the market snapshot, detected triggers, scoring inputs, risk assumptions, generated alert, manual execution record, and outcome. AI-generated analysis may summarize, explain, or compare evidence, but MUST NOT invent market facts or become the sole authority for trading decisions. Confidence scores MUST be decomposable and eventually calibratable against realized outcomes.

### V. Manual-First Execution, Automation-Compatible Architecture
The initial product sends alerts and records real manual trades from day one. It MUST separate system-generated signals from human execution decisions and actual trade outcomes. The domain model MUST remain compatible with future supervised or automated execution, but automated order placement is out of scope until explicit specs define risk limits, permissions, failure modes, kill switches, exchange constraints, and audit requirements.

### VI. Learning Requires Evidence, Versioning, and Guardrails
Self-learning MUST be implemented as a controlled feedback loop, not silent mutation. Strategy weights, scoring logic, model versions, and learning rules MUST be versioned and tied to the data that justified them. Learning changes MUST be evaluated against historical and forward results, checked for overfitting, and reversible. Post-trade analysis MUST distinguish bad thesis, bad timing, bad entry, bad stop, bad target, execution deviation, and market regime mismatch.

### VII. Industrial Maintainability for Personal Use
Although alpha-signal is a personal product, it MUST be engineered as an industrial-grade system: modular, testable, observable, secure, reproducible, and maintainable. Secrets MUST NOT be committed. Data schemas and migrations MUST be deliberate. External integrations MUST be isolated behind adapters. Runtime behavior MUST be logged with enough structure to debug signal generation, alert delivery, tracking, and learning outcomes.

## Product Constraints

- Primary market: crypto futures and perpetual futures.
- Initial execution mode: alerts plus real manual trade recording.
- Future execution mode: possible supervised or automated execution only after dedicated specs and safety controls.
- Holding period: intraday to multi-day maximum; long-duration swing/investment workflows are out of scope unless later specified.
- Asset universe: dynamic watchlist; assets qualify through liquidity, volatility, spread, data availability, risk profile, and detected opportunity quality.
- Strategy posture: selective, high-quality signals; overtrading is a product failure.
- Alert posture: alerts must include direction, instrument, thesis, triggers, confidence, entry zone or execution plan, stop, take-profit logic, invalidation, timestamp, disclaimer, and tracking identity when applicable.
- Financial posture: the product provides decision support and personal trading intelligence; it must not represent outputs as guaranteed profit or financial advice.

## Development Workflow and Quality Gates

- Every iteration starts with a Spec Kit spec and ends with verified acceptance criteria.
- Clarification MUST happen before technical planning when requirements affect trading behavior, risk, data semantics, learning, or future execution.
- Plans MUST identify domain entities, data contracts, tests, operational risks, and observability requirements.
- Tasks MUST be small enough to complete and verify independently.
- Tests MUST cover positive cases, negative/no-trade cases, edge cases, and regression cases for trading logic.
- Manual trade recording and signal tracking MUST preserve enough information for post-trade learning before any advanced ML optimization is attempted.
- Metrics MUST include quality and profitability dimensions, not only alert counts.
- Any model, strategy, or scoring change MUST be attributable to a spec, code change, model version, or configuration version.

## Governance

This constitution supersedes ad hoc implementation preferences. Specs, plans, tasks, code, and operational decisions MUST comply with these principles. Amendments require an explicit constitution update that explains the reason, impact, and migration considerations. If a spec conflicts with this constitution, the spec must be revised or the constitution must be amended first.

**Version**: 1.0.0 | **Ratified**: 2026-06-15 | **Last Amended**: 2026-06-15
