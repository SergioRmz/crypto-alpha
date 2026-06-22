# Data Model: Data Layer

**Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

This document describes the field-level precision for the three JSON Schemas in P1: `MarketContextSnapshot`, `WatchlistAsset`, and `TradingUniverse`. The JSON Schema files in `contracts/` are the authoritative machine-readable form; this document is the human-readable reference for the design decisions and edge cases.

## Entity: `MarketContextSnapshot`

A point-in-time market state for one crypto futures or perpetual futures instrument.

### Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | yes | Semver of the schema this snapshot conforms to. P1 value: `"0.1.0"`. |
| `canonical_symbol` | string | yes | `BASEQUOTE` (e.g., `"BTCUSDT"`), optionally with `@venue` suffix (e.g., `"BTCUSDT@binance"`). Pattern: `^[A-Z0-9]{4,20}(@[a-z0-9_-]{2,32})?$`. |
| `venue` | string | yes | Exchange identifier. One of a controlled set (e.g., `"binance"`, `"bybit"`, `"okx"`, `"kraken"`, `"coinbase"`, `"venue_agnostic"`). |
| `captured_at` | string | yes | ISO 8601 UTC with `Z` suffix. Pattern: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`. |
| `instrument_type` | string (enum) | yes | One of: `"perpetual"`, `"futures"`, `"options"`. P1 fixtures use `"perpetual"`. |
| `regime` | string (enum) | yes | Strict enum of 8 values. See "Regime enum" below. |
| `timeframes` | object | yes | Map of canonical timeframe → `TimeframeBar`. All 6 keys MUST be present. See "Timeframes" below. |
| `derivatives_context` | object | yes | Derivatives-specific context. See "Derivatives context" below. |
| `evidence_refs` | array of string | yes | Pointers to captured evidence. P1 fixtures reference their own filename. |
| `disclaimer_present` | boolean | yes | MUST be `true` (Constitution I). The disclaimer is rendered in P3, not stored here. |
| `notes` | string \| null | no | Free text. MUST NOT contain advisory language (Constitution I). |

### Regime enum (strict)

Exactly 8 values, lowercase snake_case:

| Value | Meaning |
|---|---|
| `trend_up` | Sustained upward price action on the dominant timeframe. |
| `trend_down` | Sustained downward price action on the dominant timeframe. |
| `range` | Bounded oscillation between identifiable support and resistance. |
| `chop` | Directionless, high-noise action with no tradable structure. |
| `manipulation_probable` | Price action inconsistent with volume, OI, or cross-venue context in ways that suggest spoofing, wicks, or stop hunts. |
| `extreme_volatility` | Realized volatility or ATR exceeds a regime-defined threshold (P2 will set the threshold). |
| `low_liquidity` | Spread, depth, or volume below tradability thresholds (P2 owns the formula). |
| `unknown` | Regime has not been classified yet. P1 fixtures are allowed to use this. |

### Timeframes

`timeframes` is an object with exactly these 6 keys (all required, all may have `null` values):

- `1m` (1 minute)
- `5m` (5 minutes)
- `15m` (15 minutes)
- `1h` (1 hour)
- `4h` (4 hours)
- `1d` (1 day)

Each value is either `null` or a `TimeframeBar` object:

| Field | Type | Required (when bar is not null) | Description |
|---|---|---|---|
| `open` | string | yes | Decimal-string. Opening price. |
| `high` | string | yes | Decimal-string. Highest price. |
| `low` | string | yes | Decimal-string. Lowest price. |
| `close` | string | yes | Decimal-string. Closing price. |
| `volume` | string | yes | Decimal-string. Volume in quote currency (e.g., USDT). |
| `realized_volatility_pct` | string \| null | no | Realized volatility (annualized) as a percentage. `null` when the input series is too short. |
| `atr_pct` | string \| null | no | ATR / price × 100. `null` when the input series is too short. |
| `bar_start_utc` | string | yes | ISO 8601 UTC with `Z`. Start of the bar window. |
| `bar_end_utc` | string | yes | ISO 8601 UTC with `Z`. End of the bar window. Must equal `captured_at` for the most-recent bar of the snapshot's primary timeframe. |

**Money-like fields use decimal-string representation**, not `float`, to avoid IEEE 754 precision loss. JSON Schema's `"pattern": "^[0-9]+(\\.[0-9]+)?$"` enforces this.

### Derivatives context

| Field | Type | Required | Description |
|---|---|---|---|
| `funding_rate` | string \| null | yes (may be null) | Current funding rate as a decimal (e.g., `"0.0001"` for 1 bps). `null` when the venue does not provide funding (e.g., dated futures) or the data is unavailable. |
| `funding_rate_next_at_utc` | string \| null | no | ISO 8601 UTC. Next funding event. `null` when not provided. |
| `open_interest` | string \| null | yes (may be null) | Open interest in contract units. `null` when unavailable. |
| `open_interest_usd` | string \| null | no | Open interest in USD. `null` when unavailable. |
| `mark_price` | string \| null | yes (may be null) | Mark price used for margining. `null` when unavailable. |
| `last_price` | string \| null | yes (may be null) | Last traded price. `null` when the venue has not reported a trade in the snapshot window. |
| `mark_last_spread_bps` | string \| null | no | `\|mark - last\| / last × 10000`. `null` when either mark or last is `null`. |
| `liquidations_24h_long_usd` | string \| null | no | 24h liquidations on the long side, USD. `null` when unavailable. |
| `liquidations_24h_short_usd` | string \| null | no | 24h liquidations on the short side, USD. `null` when unavailable. |

**Field required-but-nullable pattern**: The field is in `required` (so the key MUST be present) but its value can be `null`. This is a JSON Schema 2020-12 idiom using `type: ["string", "null"]`. It forces producers to acknowledge the field explicitly rather than silently omitting it.

### Invariants

The snapshot entity in P1 inherits from the P0 `MarketContextSnapshot` entity and adds these P1-specific contract invariants:

1. **All 6 timeframe keys MUST be present** (value may be `null`).
2. **All money-like fields use decimal-string** (no `float`, no `number`).
3. **`captured_at` MUST be UTC ISO 8601 with `Z`**.
4. **`regime` MUST be from the strict 8-value enum**.
5. **`disclaimer_present` MUST be `true`** (Constitution I).
6. **`evidence_refs` MUST be non-empty** (Invariant 11 from P0: enough evidence at decision time).
7. **No `cadence_seconds` field** (P3 owns cadence).

## Entity: `WatchlistAsset`

A tradable crypto futures or perpetual futures instrument.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | yes | Semver. P1 value: `"0.1.0"`. |
| `canonical_symbol` | string | yes | Same pattern as the snapshot. |
| `venue` | string | yes | Same enum as the snapshot. |
| `instrument_type` | string (enum) | yes | Same enum as the snapshot. |
| `asset_class` | string (enum) | yes | One of: `"crypto"`. (P1 ships crypto only; the field is future-proofed for the day, if ever, the system expands.) |
| `base_asset` | string | yes | Ticker of the underlying (e.g., `"BTC"`, `"ETH"`, `"SOL"`). |
| `quote_asset` | string | yes | Ticker of the quote currency (e.g., `"USDT"`, `"USD"`, `"USDC"`). |
| `data_availability` | object | yes | See below. |
| `eligible` | boolean | yes | Whether this asset is currently eligible for monitoring. The schema accepts `false`; runtime code (P2) is responsible for filtering. |
| `liquidity_suitability` | string \| null | no | Derived attribute, owned by P2. P1 fixtures set this to `null`. |
| `added_to_watchlist_at` | string | yes | ISO 8601 UTC. When the asset was added to the watchlist. |
| `notes` | string \| null | no | Free text. No advisory language. |

### `data_availability` subobject

| Field | Type | Required | Description |
|---|---|---|---|
| `ticker_realtime` | boolean | yes | Real-time ticker stream available. |
| `kline_history_depth_days` | integer | yes | Days of kline history available. Minimum: 30 for v1 (P2 will need history for realized-vol calculations). |
| `funding_history` | boolean | yes | Whether funding rate history is available. |
| `open_interest_history` | boolean | yes | Whether OI history is available. |
| `last_verified_at_utc` | string | yes | ISO 8601 UTC. When the data availability claims were last verified. |

## Entity: `TradingUniverse`

The total set of `WatchlistAsset` entries the system is permitted to evaluate.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | yes | Semver. P1 value: `"0.1.0"`. |
| `universe_id` | string | yes | Stable identifier (e.g., `"universe_mainnet_v1"`). |
| `generated_at` | string | yes | ISO 8601 UTC. When the universe was generated. |
| `assets` | array of `WatchlistAsset` | yes | Non-empty array. |

### Invariants

1. **`assets` MUST be non-empty.**
2. **`canonical_symbol + venue` pairs MUST be unique** within `assets`. (Enforced in the validator as a post-schema check; JSON Schema's `uniqueItems` is per-array, not per-field-pair.)
3. **At least one asset MUST have `eligible = true`.** (Post-schema check; an all-false universe is a misconfiguration.)

## Cardinality summary

| Relationship | Cardinality | Notes |
|---|---|---|
| `MarketContextSnapshot` → `WatchlistAsset` | many → one (or zero) | A snapshot for an asset not in the universe is allowed in P1; P2 will filter. |
| `TradingUniverse` → `WatchlistAsset` | one → many | The universe is a collection. |

## Field conventions (P1, inherited from P0)

- All timestamps are UTC ISO 8601 with explicit `Z` suffix.
- All money-like fields use decimal-string representation. Never `float`, never `number` (in JSON Schema, the value is the string type with a numeric pattern).
- All enum values are lowercase snake_case.
- All IDs (when introduced) are deterministic: `<entity_type>_<ulid>` for new records.
- All human-readable fields are free text, may be empty, MUST NOT contain advisory language.

## Deferred to later specs

- Per-timeframe rolling OHLCV history (R2 in research.md). P1 ships the current bar only.
- Cross-venue reconciliation (R3).
- Regime classifier (R4, P2).
- Funding/OI refresh cadence (R5, P3).
- Liquidity suitability formula (R6, P2).
- Schema versioning migration framework (R7, P3+).
- Live data integration (R8, P7+).
- Additional venue identifiers (e.g., Deribit, Bitfinex) — P1 supports a controlled set, more can be added in P3.
- Multi-tenancy and permissions — explicitly out of scope (inherited from P0).
