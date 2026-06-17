# Feature Specification: Profitable Trading Decision Domain

**Feature Branch**: `001-profitable-trading-decision-domain`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "Define the foundational product domain for crypto-alpha: a personal, industrial-grade AI-assisted crypto futures trading intelligence system governed by SDD/Spec Kit, operating on a dynamic multi-asset futures/perpetual futures watchlist, sending alerts first, recording real manual trades from day one, optimizing for high-quality risk-adjusted profitability, and remaining compatible with future supervised or automated execution."

## Clarifications

### Session 2026-06-17

The following questions were raised in the 2026-06-15 planning conversation and resolved in the 2026-06-17 session before this update. They are recorded here so the spec, plan, and any later implementation remain consistent.

- **Q1 — What counts as a "high-quality opportunity" in v1?**
  **A**: A high-quality opportunity is one that simultaneously satisfies four hard gates: (1) **clear invalidation** — a stop-loss level is identifiable in the market structure, not arbitrary; (2) **positive expected R/R** at the proposed entry — the distance to the closest take-profit must be at least 1.5× the distance to the stop; (3) **structural evidence** — at least one named setup (liquidity sweep, BOS/CHOCH, stopping volume, order block + FVG, etc.) is present in the captured snapshot; (4) **no veto** — the opportunity is not in a regime flagged as `chop`, `manipulation probable`, `extreme volatility`, or `low liquidity`. Opportunities that fail any gate are classified as `rejected` with a `rejection_reason` and never become signals. Acceptance of "no-trade" as a valid outcome is encoded in FR-015.

- **Q2 — How do we separate a system-generated signal from a real manual trade?**
  **A**: A `Signal` is the system's recommendation, generated from a confirmed opportunity. A `ManualTradeRecord` is the trader's actual execution, which may be linked to a signal, modified from a signal, or completely independent. The link is optional but explicit. Both entities carry their own `entry`, `size`, `direction`, `instrument`, and timestamps. The `TradeOutcome` records both `theoretical_signal_result` (what would have happened if the signal had been followed exactly) and `actual_manual_result` (what really happened). This separation is encoded in FR-006, FR-007, and FR-008, and validated by SC-003.

- **Q3 — What are the minimum fields the journal must capture from day one?**
  **A**: From the very first trade, every record — whether signal, manual trade, or outcome — MUST capture at least: `id` (deterministic ULID/UUID), `instrument` (canonical symbol), `direction` (`long`/`short`), `entry_price`, `entry_timestamp` (UTC), `stop_loss`, `take_profit_plan[]`, `risk_per_unit`, `size_or_normalized_exposure`, `fees_paid` (when known, otherwise `null`), `regime` (one of the named regimes), `strategy_version` (reference to the scoring or rule version that produced the decision), and `notes`. Outcomes additionally require `exit_price`, `exit_timestamp`, `realized_r_multiple`, `max_favorable_excursion`, `max_adverse_excursion`, and at least one `quality_label` (thesis, timing, entry, stop, target, execution, or regime). Optional but encouraged: `screenshot_path` and `trigger_evidence[]`. This is the v1 journal minimum; future specs may add fields but cannot remove any of these.

- **Q4 — What does "profitability" mean in v1?**
  **A**: Progressive. v1 uses **R-multiple** as the primary unit (realized R, average R, expectancy in R, profit factor in R). PnL in quote currency is recorded whenever fees and size are available, but R is the canonical metric for selection, ranking, calibration, and learning because it is normalized across instruments, sizes, and leverage. USD-quote PnL becomes a first-class reporting metric in a later spec once reliable fee and position data are flowing. This is encoded in FR-014, FR-017, and SC-008.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluate high-quality trading opportunities (Priority: P1)

As the trader, I want crypto-alpha to represent market opportunities as structured, comparable trading decisions so that I can prioritize the best risk-adjusted futures opportunities across a dynamic crypto watchlist instead of reacting to isolated alerts.

**Why this priority**: Profitability depends on selecting the best opportunities and avoiding weak ones. The domain must establish opportunity quality before any detector, dashboard, or alert channel is implemented.

**Independent Test**: Can be tested by describing multiple candidate opportunities across different assets and verifying that each can be represented with comparable quality, risk, confidence, invalidation, and profitability attributes without assuming a single symbol.

**Acceptance Scenarios**:

1. **Given** two candidate opportunities on different crypto futures instruments, **When** they are recorded in the domain model, **Then** both expose comparable attributes for direction, market context, setup thesis, risk plan, confidence, expected value, and quality status.
2. **Given** a candidate opportunity with weak liquidity, poor risk/reward, or unclear invalidation, **When** it is evaluated, **Then** the domain can classify it as not tradable or lower priority without requiring an alert to be sent.
3. **Given** a candidate opportunity that meets quality criteria, **When** it becomes actionable, **Then** the domain can produce a signal that references the originating opportunity and preserves its evidence.

---

### User Story 2 - Separate signal recommendation from real manual trade execution (Priority: P1)

As the trader, I want crypto-alpha to distinguish system-generated signals from my actual manual trades so that learning reflects what the system recommended, what I actually did, and what the market outcome was.

**Why this priority**: Real profitability cannot be learned from alerts alone. Manual execution deviations must be captured from the beginning to avoid corrupting system performance metrics.

**Independent Test**: Can be tested by recording a signal and then recording a manual trade with a different entry, size, exit, or decision status while preserving the relationship between signal, execution, and outcome.

**Acceptance Scenarios**:

1. **Given** a signal is generated, **When** the trader enters manually at a different price, **Then** the system records both the original signal plan and the actual manual execution details.
2. **Given** a signal is generated but not taken, **When** the trader records no trade, **Then** the system can still track whether the signal would have reached entry, invalidation, target, or stop.
3. **Given** the trader closes a manual trade early, **When** the outcome is recorded, **Then** the system distinguishes manual exit quality from the original signal thesis quality.

---

### User Story 3 - Track outcome quality for learning (Priority: P1)

As the trader, I want every completed signal or manual trade to produce a learning-ready outcome so that crypto-alpha can improve based on evidence rather than impressions.

**Why this priority**: Auto-learning cannot be trustworthy without accurate outcome semantics and post-trade labels.

**Independent Test**: Can be tested by taking completed examples and verifying that the domain can label thesis quality, timing quality, entry quality, stop quality, target quality, and execution deviation separately.

**Acceptance Scenarios**:

1. **Given** a signal hits stop loss quickly after entry, **When** the outcome is analyzed, **Then** the domain supports labels for bad thesis, bad timing, bad stop placement, or valid loss depending on evidence.
2. **Given** a signal direction is correct but the entry is missed, **When** the outcome is analyzed, **Then** the system can record directionally correct but not executed rather than treating it as a normal win or loss.
3. **Given** a manual trade differs from the signal, **When** profitability is calculated, **Then** the system can report signal theoretical performance and actual manual trade performance separately.

---

### User Story 4 - Preserve future execution compatibility without enabling automation (Priority: P2)

As the trader, I want the domain to be compatible with future supervised or automated execution while keeping the initial product alert-only so that early decisions do not block future evolution.

**Why this priority**: Execution automation requires safety controls and explicit specs later, but the foundational model must not make future execution impossible.

**Independent Test**: Can be tested by verifying that a signal contains enough structured intent to become an order plan later while no requirement permits automatic order placement in this spec.

**Acceptance Scenarios**:

1. **Given** a signal is created, **When** its execution intent is inspected, **Then** it contains direction, instrument, entry logic, stop logic, target logic, invalidation, and risk constraints.
2. **Given** no automation-specific safety spec exists, **When** a signal is generated, **Then** it cannot be treated as authorization to place an order automatically.

---

### Edge Cases

- A candidate opportunity appears on an illiquid altcoin with attractive chart structure but unacceptable spread or execution risk.
- A futures instrument lacks reliable funding, open interest, liquidation, or contract metadata at evaluation time.
- A signal reaches target before the trader manually enters.
- A signal invalidates before reaching the entry zone.
- A manual trade is opened without any prior system signal and still needs to be journaled.
- A manual trade partially fills, scales in, scales out, or exits in multiple parts.
- Mark price, last price, and exchange execution price disagree materially.
- A setup remains open longer than the intended intraday-to-multi-day holding horizon.
- Multiple correlated assets produce simultaneous opportunities and only one should be prioritized.
- A high-confidence setup fails; the outcome must preserve evidence for calibration rather than overwriting the original confidence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define a dynamic trading universe for crypto futures and perpetual futures rather than assuming one fixed asset.
- **FR-002**: System MUST represent a watchlist asset with enough information to evaluate tradability, including symbol, venue eligibility, derivatives type, liquidity suitability, volatility suitability, and data availability status.
- **FR-003**: System MUST represent an opportunity before it becomes a signal, including instrument, direction, timeframe context, thesis, detected triggers, market regime, quality status, and reason for rejection when not tradable.
- **FR-004**: System MUST represent a signal as an actionable recommendation derived from an opportunity, including tracking identity, direction, instrument, strategy/thesis, triggers, confidence, entry logic, stop logic, target logic, invalidation, timestamp, and disclaimer status.
- **FR-005**: System MUST represent risk plans independently from alert text, including entry zone or entry condition, stop loss, take-profit plan, risk/reward expectations, maximum intended holding period, and invalidation criteria.
- **FR-006**: System MUST distinguish theoretical signal performance from actual manual trade performance.
- **FR-007**: System MUST support manual trade records from day one, including entry, exit, position direction, instrument, size or normalized exposure, leverage when used, fees when available, timestamps, relationship to signal when applicable, and manual notes.
- **FR-008**: System MUST allow manual trades that are linked to a signal, manually modified from a signal, or independent from any signal.
- **FR-009**: System MUST classify lifecycle state for opportunities, signals, and manual trades so that waiting, active, invalidated, expired, closed, analyzed, and learning-ready states are distinguishable.
- **FR-010**: System MUST support outcome records that capture realized result, theoretical result, maximum favorable excursion, maximum adverse excursion, time in trade or signal, target/stop interaction, invalidation, and quality labels.
- **FR-011**: System MUST capture enough evidence at decision time to audit why an opportunity, signal, confidence score, or rejection occurred.
- **FR-012**: System MUST support confidence as a decomposable assessment rather than an opaque number.
- **FR-013**: System MUST support learning observations that can reference original evidence, outcome labels, execution deviations, and suggested future adjustments without silently changing strategy behavior.
- **FR-014**: System MUST define profitability metrics that prioritize quality, including expectancy, average R, profit factor, drawdown, fees/slippage impact, win rate by quality bucket, and confidence calibration.
- **FR-015**: System MUST treat no-trade decisions as first-class outcomes when an opportunity is rejected or avoided for valid quality/risk reasons.
- **FR-016**: System MUST support future execution intent as structured data while prohibiting automatic order placement until a later execution-specific spec authorizes it.
- **FR-017**: System MUST enforce the intended holding horizon as intraday to multi-day maximum in the domain semantics.
- **FR-018**: System MUST preserve version references for strategy logic, scoring logic, model logic, or manual rules used at decision time.

### Key Entities *(include if feature involves data)*

- **TradingUniverse**: The total set of instruments the system may evaluate, filtered by market type, venue, data availability, and risk constraints.
- **WatchlistAsset**: A tradable crypto futures or perpetual futures instrument currently eligible for monitoring or ranking.
- **MarketContextSnapshot**: A point-in-time summary of market conditions used to evaluate an opportunity, including timeframe context and derivatives-specific context when available.
- **Opportunity**: A potential trade idea detected or entered for evaluation before becoming an actionable signal.
- **Signal**: A structured recommendation emitted by the system when an opportunity meets quality and actionability criteria.
- **RiskPlan**: The proposed trade management structure, including entry, stop, targets, invalidation, and intended holding period.
- **ConfidenceScore**: A decomposable confidence assessment with components, penalties, and version reference.
- **ManualTradeRecord**: The trader's actual manual execution record, whether linked to a signal or independent.
- **TradeOutcome**: The measured result of a signal and/or manual trade, including profitability, lifecycle result, excursions, and quality labels.
- **LearningObservation**: A post-outcome record that captures what the system should learn or review without automatically mutating future behavior.
- **StrategyVersion**: A reference to the strategy, scoring, model, or rule version used when the decision was made.
- **ExecutionIntent**: A future-compatible structured representation of what would need to be executed, without authorizing automation in this spec.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of recorded signals can be traced back to an originating opportunity, risk plan, confidence score, and evidence snapshot.
- **SC-002**: 100% of manual trades can be recorded either linked to a signal or explicitly marked as independent.
- **SC-003**: For any completed signal/manual trade pair, the system can report theoretical signal result and actual manual trade result separately.
- **SC-004**: At least five representative edge-case examples can be modeled without adding new top-level domain concepts.
- **SC-005**: Every opportunity can end in one of three business outcomes: promoted to signal, rejected/no-trade with reason, or expired/unresolved.
- **SC-006**: Every completed outcome can carry at least one quality label distinguishing thesis, timing, entry, stop, target, execution, or market-regime issues.
- **SC-007**: No domain concept requires automatic exchange order placement to deliver value in the initial alert/manual-trade workflow.
- **SC-008**: Profitability reporting can include expectancy, average R, profit factor, and drawdown concepts without relying only on win rate.

## Assumptions

- The initial user is a single personal trader; multi-user SaaS, billing, permissions, and customer management are out of scope.
- The initial market scope is crypto futures and perpetual futures, not spot investing.
- The system starts with alerts and manual trade journaling; automated execution requires a future dedicated spec.
- Trades are intended to last intraday to a few days maximum.
- The initial system may use normalized exposure or R-multiple tracking when exact position sizing, fees, or leverage details are unavailable.
- AI assistance is allowed for explanation, summarization, comparison, and post-trade analysis, but market facts and scoring inputs must be grounded in captured evidence.
- The first implementation may use a limited set of venues or data sources as long as the domain does not assume one permanent provider.
