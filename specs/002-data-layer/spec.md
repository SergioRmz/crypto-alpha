# Feature Specification: Data Layer (Market Snapshot Contract & Fixtures)

**Feature Branch**: `002-data-layer`

**Created**: 2026-06-21

**Status**: Draft

**Input**: User description: "Define the data layer for crypto-alpha: JSON Schemas for `MarketContextSnapshot`, `WatchlistAsset`, and `TradingUniverse`; deterministic sample fixtures for BTC, ETH, and SOL perpetuals; a local validator script that confirms fixtures conform to the schemas and the P0 invariants. No live exchange APIs, no persistence layer, no scoring logic — strictly contract + fixtures + validator."

## Clarifications

### Session 2026-06-21

The following design decisions were resolved before authoring this spec, in alignment with the P0 constitution and the P0/P1 handoff defined in `spec-001/plan.md`.

- **C1 — Snapshot granularity**: A single `MarketContextSnapshot` represents one instrument at one `captured_at` timestamp, but it **carries the timeframe context inline as a keyed map** (one entry per canonical timeframe). This keeps the snapshot self-contained for P2 scoring without requiring cross-snapshot joins. *(Resolves design question #1.)*
- **C2 — Canonical timeframes**: `[1m, 5m, 15m, 1h, 4h, 1d]`. All six MUST be present in every snapshot. Missing timeframes MUST be represented as an explicit `null` entry, never omitted. *(Resolves #2.)*
- **C3 — Derivatives context in v1**: `funding_rate`, `open_interest`, `mark_price`, `last_price`, `mark_last_spread_bps`, and `liquidations_24h` are all first-class fields in v1. They MAY be `null` when a venue or asset does not provide them, but the field MUST be present. This satisfies Constitution III ("MUST model funding, OI, mark vs last, liquidations") without inventing fake values. *(Resolves #3.)*
- **C4 — Regime enum**: Strict enum of exactly 8 values: `trend_up`, `trend_down`, `range`, `chop`, `manipulation_probable`, `extreme_volatility`, `low_liquidity`, `unknown`. The P2 regime classifier is responsible for moving assets out of `unknown`; P1 fixtures are allowed to use `unknown` for assets where no classifier has run yet. *(Resolves #4.)*
- **C5 — Volatility fields**: Two required fields per timeframe: `realized_volatility_pct` (window = 20 periods of that timeframe) and `atr_pct` (ATR/price × 100). Both are nullable when the input series is too short to compute them. *(Resolves #5.)*
- **C6 — Liquidity suitability**: The `liquidity_suitability` field on `WatchlistAsset` is a derived attribute, NOT a primary input. P1 leaves it `null` and notes in the field description that P2 (scoring engine) is the owner. *(Resolves #6.)*
- **C7 — Canonical symbol format**: `BASEQUOTE` (e.g., `BTCUSDT`) with an optional `@venue` suffix for cross-venue disambiguation (e.g., `BTCUSDT@binance`). When a fixture is venue-agnostic, the suffix is omitted. *(Resolves #7.)*
- **C8 — Validator stack**: Python 3.11+ standard library plus `jsonschema` (4.x) as the only external dependency. No `pydantic`, no `marshmallow`, no `attrs`. The schema is the contract; the validator is mechanical. *(Resolves #8.)*
- **C9 — Fixture determinism**: All fixture timestamps are hard-coded ISO 8601 UTC with explicit `Z` suffix. No randomness, no `datetime.now()`, no environment-dependent values. A fixture validated today MUST validate identically in 2028. *(Resolves #9.)*
- **C10 — Out-of-scope in P1**: `cadence_seconds` is NOT a field in P1. The cadence at which snapshots are produced is a P3 concern (signal generator). P1 produces a single, point-in-time artifact. *(Resolves #10.)*
- **C11 — Multi-asset coverage**: Fixtures MUST include BTC, ETH, and SOL perpetuals. Including SOL in P1 prevents the data layer from being silently BTC-tilted in early P2 development. *(Resolves multi-asset question.)*
- **C12 — Python language choice**: Confirmed. Python 3.11+ is the implementation language for the validator and (going forward) the runtime. Justification recorded in the design discussion thread; the short version is that every CPU-bound operation crypto-alpha needs (dataframe math, indicators, validation) has a C/Rust core, so Python is the right glue without paying the development cost of Go/Rust/C++.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Author and validate a market snapshot (Priority: P1)

As the next-phase developer, I want a JSON Schema for `MarketContextSnapshot` so that I can author or consume snapshots with confidence that the structure is stable, validated, and documented.

**Why this priority**: Every downstream phase (P2 scoring, P3 signals, P5 outcomes) consumes snapshots. The schema is the single most important contract in the data layer.

**Independent Test**: Can be fully tested by writing a snapshot JSON file that conforms to the schema and running the validator; the validator exits 0. Conversely, writing a malformed snapshot and running the validator produces a clear, line-referenced error and exits non-zero.

**Acceptance Scenarios**:

1. **Given** a snapshot JSON that matches the schema, **When** the validator runs, **Then** it exits 0 and prints `OK` with a per-snapshot summary.
2. **Given** a snapshot JSON with a missing required field, **When** the validator runs, **Then** it exits non-zero, prints the file path, the missing field path, and a human-readable error.
3. **Given** a snapshot JSON with an invalid `regime` value (not in the enum), **When** the validator runs, **Then** it exits non-zero and names the offending value.

---

### User Story 2 - Cover the watchlist with multi-asset fixtures (Priority: P1)

As the next-phase developer, I want deterministic BTC, ETH, and SOL perp fixtures so that P2 (scoring engine) can be developed and tested against realistic, multi-asset inputs from day one — without being BTC-tilted.

**Why this priority**: Constitution III explicitly prohibits BTC-only assumptions. Shipping P1 with three assets is the cheapest way to enforce that discipline.

**Independent Test**: Can be tested by reading the three fixtures and confirming: (a) each one is syntactically valid; (b) each one passes the validator; (c) the asset universe spans different market-cap and liquidity tiers.

**Acceptance Scenarios**:

1. **Given** the three BTC, ETH, and SOL fixtures, **When** the validator runs against all of them, **Then** all three pass.
2. **Given** the three fixtures, **When** a reviewer diffs the `regime` field across them, **Then** at least two distinct regime values are present (proving the fixtures are not copy-paste with find-replace).

---

### User Story 3 - Define a watchlist and a trading universe (Priority: P2)

As the next-phase developer, I want JSON Schemas for `WatchlistAsset` and `TradingUniverse` so that the data layer can express "which assets are eligible" without coupling to any specific venue's API.

**Why this priority**: The watchlist is the dynamic filter that feeds P2 scoring. Without a schema, the scoring engine would have to invent its own list and P0's "dynamic watchlist" requirement would be aspirational, not enforced.

**Independent Test**: Can be tested by constructing a `TradingUniverse` JSON containing three `WatchlistAsset` entries (BTC, ETH, SOL) and validating it against the schema.

**Acceptance Scenarios**:

1. **Given** a `TradingUniverse` JSON with three `WatchlistAsset` entries, **When** the validator runs, **Then** it exits 0 and the cardinality matches what was authored.
2. **Given** a `WatchlistAsset` with `eligible = false`, **When** the validator runs, **Then** the entry is still accepted (eligibility is a runtime filter, not a schema constraint), and the schema notes the field's semantic role.

---

### Edge Cases

- A snapshot is authored for a symbol not in any `TradingUniverse` (orphan snapshot). The snapshot schema does not enforce universe membership — that is a P2 concern. P1 documents this as an explicit non-constraint.
- A snapshot's `captured_at` is in the future (clock skew, bad authoring). The schema accepts any ISO 8601 UTC string; P1 does not enforce temporal sanity. A future spec (P2 or later) may add a `validate_freshness` helper that checks `captured_at` against `now()`.
- A snapshot is missing one or more timeframes entirely (key absent from the map). The schema requires the key to be present with a `null` value; omitting the key is a schema violation.
- A fixture uses a regime value not in the enum. Schema rejection with the offending value named.
- A fixture has `mark_price` but `last_price = null`. Allowed by the schema (the field is nullable); the validator does not infer or cross-fill.
- A `WatchlistAsset` references a venue that does not exist in any real exchange. Allowed by the schema; the schema validates structure, not external reality.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define a JSON Schema for `MarketContextSnapshot` that enforces: required fields `schema_version`, `canonical_symbol`, `venue`, `captured_at`, `instrument_type`, `regime`, `timeframes`, `derivatives_context`, and `evidence_refs[]`.
- **FR-002**: System MUST require that the `timeframes` field is an object whose keys are drawn from the exact set `[1m, 5m, 15m, 1h, 4h, 1d]`, with each key present (value MAY be `null`).
- **FR-003**: System MUST define a JSON Schema for `WatchlistAsset` that enforces: required fields `canonical_symbol`, `venue`, `instrument_type`, `asset_class`, `data_availability`, and `eligible`.
- **FR-004**: System MUST define a JSON Schema for `TradingUniverse` that enforces: required fields `schema_version`, `universe_id`, `generated_at`, and `assets[]` (non-empty array of `WatchlistAsset`).
- **FR-005**: System MUST require that `regime` values come from a strict enum of exactly 8 values: `trend_up`, `trend_down`, `range`, `chop`, `manipulation_probable`, `extreme_volatility`, `low_liquidity`, `unknown`.
- **FR-006**: System MUST provide three deterministic sample fixtures (BTC, ETH, SOL perpetuals) that pass the validator without modification.
- **FR-007**: System MUST provide a local validator script (`scripts/validation/validate_data_layer.py`) that accepts a list of JSON files and a directory of schemas, validates every file against its corresponding schema, and exits 0 only when all files are valid.
- **FR-008**: System MUST use Python 3.11+ standard library plus `jsonschema` (4.x) as the only runtime dependencies. No `pydantic`, no `marshmallow`.
- **FR-009**: System MUST NOT call any external network endpoint, exchange API, or live data source. All validation MUST be reproducible from a clean clone with no network access.
- **FR-010**: System MUST produce deterministic validation output. Given the same inputs, the validator MUST produce byte-identical stdout and exit code across runs.
- **FR-011**: System MUST encode the P0 invariants (Invariants 1, 8, 9 from `spec-001/data-model.md`) as much as the JSON Schema syntax allows. Specifically, the snapshot schema MUST require `schema_version` and `captured_at` (UTC ISO 8601 with `Z`).
- **FR-012**: System MUST reject, at validation time, any advisory language in human-readable fields (`thesis`, `notes`, `execution_deviation_notes`) that would violate Constitution I. *In P1, this is enforced by the absence of such fields in the snapshot schema; the journal fields belong to P4–P5.*
- **FR-013**: System MUST NOT introduce a `cadence_seconds` field in any P1 artifact. P3 is the owner of cadence.
- **FR-014**: System MUST keep `liquidity_suitability` as `null` in every P1 fixture, with a JSON Schema comment noting that P2 (scoring engine) is the owner of this derived field.
- **FR-015**: System MUST document, in `quickstart.md`, how to reproduce the validation from a clean clone, including the exact `uv` commands to set up the venv and install `jsonschema`.

### Key Entities *(include if feature involves data)*

- **MarketContextSnapshot** *(P0 entity, schema-anchored in P1)*: Point-in-time market state for one instrument, containing inline per-timeframe data, derivatives context, and evidence references.
- **WatchlistAsset** *(P0 entity, schema-anchored in P1)*: A tradable crypto futures or perpetual futures instrument, with eligibility and data availability flags.
- **TradingUniverse** *(P0 entity, schema-anchored in P1)*: The total set of `WatchlistAsset` entries the system is permitted to evaluate at a given moment.
- **SchemaContract** *(P1-introduced)*: A single JSON Schema file under `specs/002-data-layer/contracts/` that the validator binds to one of the three entities above.
- **FixtureArtifact** *(P1-introduced)*: A single deterministic JSON file under `specs/002-data-layer/fixtures/` that conforms to a `SchemaContract` and is used as test data for P2 and beyond.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the three P1 fixtures (`btc-perp-snapshot.json`, `eth-perp-snapshot.json`, `sol-perp-snapshot.json`) pass the validator with exit code 0.
- **SC-002**: The validator produces a non-zero exit code and a named error for each of the following deliberate violations: missing required field, wrong type, invalid enum value, missing timeframe key. Each violation is a separate unit test fixture (not yet introduced in P1, but the validator MUST support them; the unit tests land in a later spec).
- **SC-003**: The three JSON Schemas (`snapshot.schema.json`, `watchlist-asset.schema.json`, `trading-universe.schema.json`) are all present, all parseable by `jsonschema`, and all referenced from `scripts/validation/validate_data_layer.py`.
- **SC-004**: Running the validator against the three fixtures prints exactly 3 `OK` lines and exits 0, with no warnings.
- **SC-005**: From a clean clone on a machine with `uv` installed, the entire validation flow (venv creation, dependency install, validator run) completes in under 30 seconds and under 50 MB of disk.
- **SC-006**: Zero secrets, credentials, API keys, or live URLs appear in any P1 artifact. `grep -RIn 'sk-\|api_key\|secret\|live\.' specs/002-data-layer/ scripts/validation/` returns 0 matches.
- **SC-007**: The P0 constitution check from `spec-001/plan.md` is re-evaluated in `specs/002-data-layer/plan.md` and re-confirmed for all seven principles.

## Assumptions

- Python 3.11+ is available on the target developer workstation, either via system install or `uv`.
- `uv` is the canonical Python package manager for this project (documented in `quickstart.md`).
- The next phase (P2: scoring engine) will consume these fixtures as test data, not as live inputs.
- The `TradingUniverse` schema does not need to enforce cross-venue consistency (e.g., that `BTCUSDT@binance` and `BTCUSDT@bybit` are listed separately). P1 documents the venue suffix convention; cross-venue bookkeeping is a later spec.
- Snapshot freshness (how stale is too stale) is a P3+ concern. P1 only requires that `captured_at` be present and parseable.
- A `WatchlistAsset.eligible = false` entry is still semantically valid in P1; runtime code (P2) is responsible for filtering. The schema accepts both.
- The fixtures are synthetic but plausible. They are NOT real market data and MUST NOT be mistaken for such. A `disclaimer_present` field is required on every snapshot (inherited from P0 FR-004's `Signal.disclaimer_present`; applied here to `MarketContextSnapshot.disclaimer_present = true` for consistency).
