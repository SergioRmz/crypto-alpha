# Research: Data Layer Design Decisions

**Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

This document captures the design precedents, the "why this shape" reasoning, and the open research questions deferred to later specs. It is the Phase 0 output of the planning workflow.

## Why a contract-first data layer?

The P0 spec defined the **entity vocabulary** of crypto-alpha: 12 entities including `MarketContextSnapshot`, `WatchlistAsset`, and `TradingUniverse`. P0 is language-agnostic and has no JSON Schemas — that is intentional, because a contract is a different artifact from a definition.

P1's job is to take three of those entities and turn them into **mechanically enforceable contracts**. Once a JSON Schema exists, the data layer has:

1. **Stable input shape** for P2 (scoring engine) to develop against.
2. **A test oracle** for P2 to verify its outputs against (snapshots it consumes must match this schema; snapshots it produces must also match this schema).
3. **A documentation artifact** that doubles as a typed contract (autocomplete, validation, codegen in later phases).
4. **A regression firewall**: any change to the data shape requires a `schema_version` bump and a coordinated fixture update, surfacing breakages early.

## Precedent scan

The "JSON Schema for market data" pattern is well-trodden in the trading systems space. Three reference shapes informed this design:

### A. CCXT unified market data

`ccxt` (the de-facto exchange connector library) normalizes market data across 100+ exchanges. Its per-symbol `ticker`, `ohlcv`, and `orderBook` shapes are minimalist (a few fields) and venue-agnostic. We borrow the **venue-agnostic with optional venue suffix** convention: `BTCUSDT` for venue-agnostic, `BTCUSDT@binance` for venue-specific.

**Where we differ**: `ccxt` is dynamically typed (Python dicts). We need a JSON Schema for static validation, so we add explicit types, required fields, and enums.

### B. Tardis Machine / Databento schemas

Tardis and Databento ship JSON Schemas (or protobufs) for normalized crypto market data. Their shapes are richer than `ccxt`'s but they all share one feature: **timeframe-keyed maps** for OHLCV data. We adopt this pattern for the `timeframes` field in the snapshot.

**Where we differ**: Tardis and Databento model historical replay data (microsecond granularity, order book L2, trade ticks). We do not need that fidelity in v1 — we snapshot at human timeframes (1m to 1d) and capture the **current state**, not the full tape. P7+ (if ever) can add L2 book data behind an extension schema.

### C. Nautilus Trader domain models

Nautilus Trader is a Rust/Python hybrid trading platform with a richly-typed domain model. Its `Instrument` and `Bar` types enforce field-level invariants. We borrow the **strict-typing and explicit-enum** discipline.

**Where we differ**: Nautilus is a full execution framework. We are a personal trading intelligence system. We borrow the typing discipline, not the execution machinery (which P0 explicitly defers).

## Design decisions and rationale

### D1. Snapshot = one instrument, multi-timeframe

**Decision**: A single `MarketContextSnapshot` represents one `(canonical_symbol, venue, captured_at)` triple. It carries the timeframe context inline as a keyed map.

**Rationale**: This keeps the snapshot self-contained for P2 scoring. P2's confluence math needs to compare across timeframes (e.g., "is the 1h trend aligned with the 4h trend?"). Requiring P2 to join multiple single-timeframe snapshots would force a join key, a clock-skew tolerance, and a "what if one timeframe is missing?" reconciliation policy. Pushing all of that into the snapshot (with explicit `null` for missing timeframes) makes the contract self-describing and the downstream math simpler.

**Trade-off**: Larger payload per snapshot (six timeframe entries even if some are `null`). For a personal system with three to ten assets, this is negligible. For a 100-asset universe polled every second, it would matter — but that is P7+ territory.

### D2. Canonical timeframes set in v1

**Decision**: `[1m, 5m, 15m, 1h, 4h, 1d]`.

**Rationale**: Six timeframes cover the intraday-to-multi-day holding horizon from P0 (Constitution: "intraday to multi-day maximum"). They map cleanly to common venue API parameters (Binance kline intervals are exactly these six). They are the smallest set that lets P2's confluence math compare short-term structure against longer-term trend.

**Trade-off**: Some traders want 3m, 12m, 2h, 6h, 8h, 12h, 1w. None of those are in v1. They are easy to add later (the schema is keyed, not enumerated) if a real scoring need emerges.

### D3. Derivatives context in v1, null-allowed

**Decision**: `funding_rate`, `open_interest`, `mark_price`, `last_price`, `mark_last_spread_bps`, `liquidations_24h` are all first-class fields. They MAY be `null` when the venue or asset does not provide them.

**Rationale**: Constitution III explicitly says the system "MUST model" these when available. Shipping the fields as nullable satisfies the principle without inventing fake values. A `null` is honest; a synthesized zero is a lie.

**Trade-off**: P2 will need null-tolerant math (e.g., `if funding_rate is None: skip funding-based gates`). This is a known P2 design constraint; P1 just makes the contract honest.

### D4. Strict regime enum, 8 values

**Decision**: Exactly 8 values: `trend_up`, `trend_down`, `range`, `chop`, `manipulation_probable`, `extreme_volatility`, `low_liquidity`, `unknown`.

**Rationale**: The P0 spec listed 7 regimes. We add `unknown` as a fallback so that P1 fixtures do not have to invent regime classifications (which are P2's job). The enum is strict (closed world) to prevent typos like `"trending_up"` or `"choppy"` from silently passing validation.

**Trade-off**: Adding a new regime in a future spec requires a schema version bump. That is the point — regimes are a contract surface, and the contract should change deliberately.

### D5. Volatility = realized_volatility_pct + atr_pct

**Decision**: Two required fields per timeframe. `realized_volatility_pct` (window = 20 periods of that timeframe, log-returns stdev × sqrt(annualization factor)). `atr_pct` (Average True Range / price × 100). Both nullable when the input series is too short.

**Rationale**: Two complementary views. Realized volatility is a return-based measure (good for distribution and tail-risk thinking). ATR is a price-range-based measure (good for stop placement, which is a P3 concern but informed by P1's data shape). Having both lets P2's scoring use whichever is more appropriate for a given setup, and lets P3's risk plan derive stops from `atr_pct` directly.

**Trade-off**: Two fields means two computation paths in the data ingestion (which does not exist yet). P3 or P4 will own that. P1 just specifies the shape.

### D6. `liquidity_suitability` = null in P1

**Decision**: The field exists in the schema (so P2 can fill it) but every P1 fixture sets it to `null`.

**Rationale**: Liquidity suitability is a **derived** attribute (it depends on multiple inputs: spread, depth, volume, slippage estimates). P1 has no data ingestion. Setting it to `null` in fixtures prevents P2 from accidentally treating a hard-coded zero as a real measurement.

**Trade-off**: P2 must handle `null` for this field. P1 documents this as a hard constraint on the scoring engine's input contract.

### D7. Symbol format: `BTCUSDT@venue`

**Decision**: `BASEQUOTE` (e.g., `BTCUSDT`) as the canonical symbol, with an optional `@venue` suffix for cross-venue disambiguation (e.g., `BTCUSDT@binance`).

**Rationale**: Matches the most common on-chain convention (`BTCUSDT` is what every exchange API uses). The `@venue` suffix is human-readable and avoids collisions when the same pair exists on multiple venues (e.g., `BTCUSDT@binance` vs `BTCUSDT@bybit`).

**Trade-off**: Some exchanges use different conventions (`XBTUSD` at Kraken, `BTC-USD` at Coinbase). The schema accepts the suffix but does not enforce a particular exchange's native format. P3+ (data ingestion) will own the translation from venue-native to canonical.

### D8. `jsonschema`, not `pydantic`

**Decision**: Use `jsonschema` 4.x as the only external runtime dependency. No `pydantic`, no `marshmallow`, no `attrs`.

**Rationale**: Three reasons:
1. **Language-agnostic contract.** A JSON Schema is a JSON file. P2 (scoring engine, Python), P3 (signal generator, Python), and P7+ (dashboard, possibly TypeScript) can all consume the same contract. A `pydantic` model is Python-only.
2. **Smaller dependency footprint.** `pydantic` pulls in `typing_extensions`, `annotated-types`, `pydantic-core` (Rust binary). `jsonschema` pulls in `rpds-py` and `referencing`. Both have Rust cores; `jsonschema`'s is smaller.
3. **Mechanical validation.** The validator's job is to enforce the contract. `pydantic`'s coercion, default-value injection, and validator-decorator ergonomics are not needed and would add cognitive overhead.

**Trade-off**: Error messages from `jsonschema` are less polished than `pydantic`'s. P1 mitigates this with a custom error formatter in `validate_data_layer.py`.

### D9. Deterministic fixtures

**Decision**: Every timestamp in every fixture is a hard-coded ISO 8601 UTC string with `Z` suffix. No `datetime.now()`, no randomization, no environment-dependent values.

**Rationale**: A fixture validated today MUST validate identically in 2028. If a future CI run gets a different result, the diff is a real change to the schema or the fixture, not clock drift.

**Trade-off**: Fixtures go stale. As real market conditions change, the values stop being plausible. P1's scope is "data layer works"; keeping fixtures fresh is a maintenance task the author (you) owns manually. A future spec may add a "fixture refresh" workflow, but P1 does not need it.

### D10. No `cadence_seconds` in P1

**Decision**: The field does not exist in the snapshot schema.

**Rationale**: Cadence is a property of the **data producer** (how often a snapshot is captured), not of the snapshot itself. P1 is a single, point-in-time artifact. P3 (signal generator) is the first spec that needs cadence, because cadence determines the polling loop.

**Trade-off**: P2 will need to know how fresh a snapshot is to decide whether to score it. P2 will compare `captured_at` to `now()` and reject stale snapshots itself. This is fine; freshness is a runtime concern, not a schema concern.

### D11. Three fixtures, not one

**Decision**: BTC, ETH, and SOL perpetual futures.

**Rationale**: Constitution III prohibits BTC-only assumptions. P1 is the cheapest place to enforce multi-asset discipline. Three assets is the smallest set that spans market-cap tiers (large, large, mid) and prevents the scoring engine from being developed against a single-asset worldview.

**Trade-off**: Three fixtures is more work than one. But each fixture is ~50 lines of JSON, so the marginal cost is low. The benefit is that P2 cannot be developed in a BTC-only lane without explicit override.

### D12. Python 3.11+ as the runtime language

**Decision**: Confirmed in spec clarification C12.

**Rationale** (full version in the design discussion thread):
- Every CPU-bound operation crypto-alpha needs (dataframe math via Polars/pandas, indicators via TA-Lib, JSON validation via `jsonschema`/Rust core) has a native (C/Rust) implementation. Python is the glue, not the hot path.
- The async story (`asyncio`, `aiohttp`, `FastAPI`) is mature and competitive with Node/Go for I/O-bound work.
- The ML stack (scikit-learn, XGBoost, LightGBM, HuggingFace) is Python-only and unmatched elsewhere.
- The exchange-connector stack (`ccxt`) is Python-first and ports to other languages lag by 1-2 years.
- Personal-product constraint: time-to-feature matters more than peak throughput. Python wins on iteration speed.

**Trade-off**: If the system ever needs sub-millisecond latency on a hot path (HFT, market making), Python will be the wrong choice. crypto-alpha is alert-based with intraday-to-multi-day holding; it does not need that latency.

## Open research questions (deferred)

These are intentionally NOT resolved in P1. They are recorded so the next phase knows what to investigate.

### R1. Snapshot freshness tolerance

How stale is too stale? A 1-minute-old snapshot is fine for a 4h-timeframe scoring decision. A 1-minute-old snapshot is useless for a 1m-timeframe scoring decision. P2 will need a per-timeframe staleness policy. P1 does not.

### R2. Per-timeframe data depth

Should the `timeframes` map carry the last N bars of OHLCV data, or just a single "current" bar? P1 includes only the current bar (the "snapshot" semantic). P2 or P3 may decide they need a rolling window of N bars. If so, the schema will be extended; P1 keeps the door open with the keyed-map structure.

### R3. Cross-venue universe reconciliation

If `BTCUSDT@binance` and `BTCUSDT@bybit` are both in the `TradingUniverse`, should the system treat them as the same instrument or different? P1 documents the convention but does not enforce a policy.

### R4. Regime classifier (P2)

How does the regime get assigned? P1 fixtures use `unknown`. P2 is responsible for replacing that with a real classification. The classifier's design (rules-based, ML-based, hybrid) is P2's call.

### R5. Funding/OI refresh cadence

Funding rates update every 1-8 hours depending on the venue. OI updates continuously. P1 stores whatever value is current at `captured_at`. P3+ will own the cadence question.

### R6. Liquidity suitability formula (P2)

`liquidity_suitability` is `null` in P1. P2 will define the formula (likely: spread × depth × volume, normalized). P1 does not constrain the formula beyond "the field exists and is nullable."

### R7. Schema versioning policy

When the schema changes, what is the migration path? P1 ships `schema_version: "0.1.0"`. Future schema changes MUST bump the major version, and a migration script is required. P1 does not write the migration framework; that is a P3+ concern (when there is real data to migrate).

### R8. Live data integration

Out of scope for P1. When P7+ introduces live data, the design must preserve the contract: live snapshots MUST match the same JSON Schema. The contract is the integration point, not a one-off shape.

## Summary

P1 is intentionally small. Three schemas, three fixtures, one validator. The design decisions above explain why each shape is what it is. The open research questions are documented so the next phases know what to investigate, but they do NOT block P1.
