# Quickstart: Data Layer (P1)

**Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data Model**: [data-model.md](./data-model.md) | **Research**: [research.md](./research.md)

This quickstart is for anyone (you, two months from now, a future agent session) wanting to reproduce the data layer validation from a clean clone. Read it before opening the next spec against this domain.

## What this feature is

This is the **first runtime artifact** of crypto-alpha: three JSON Schemas (the contracts), three deterministic multi-asset fixtures (the test data), and a local Python validator (the enforcement). It is the smallest possible layer that lets P2 (scoring engine) be developed without depending on a live exchange.

If you are looking for signals, alerts, scoring, or live data, you are in the wrong place. Check [plan.md](./plan.md) for the roadmap to P2.

## What to read, in order

1. [`../../.specify/memory/constitution.md`](../../.specify/memory/constitution.md) — the principles this spec is constrained by.
2. [spec.md](./spec.md) — the feature specification, including the 12 clarifications resolved on 2026-06-21.
3. [plan.md](./plan.md) — the technical context, constitution check, and project structure.
4. [research.md](./research.md) — the "why this shape" reasoning for every design decision.
5. [data-model.md](./data-model.md) — the field-level precision for the three schemas.
6. [checklists/requirements.md](./checklists/requirements.md) — the spec quality gate.
7. `contracts/*.schema.json` — the authoritative machine-readable forms.
8. `fixtures/*.json` — the deterministic sample data.

## How to reproduce validation from a clean clone

Requires Python 3.11+ (or `uv` to manage it) and ~30 seconds.

```bash
# 1. Clone (or cd into an existing clone)
cd /workspace/crypto-alpha
git checkout 002-data-layer

# 2. Create venv and install the only external dep
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e .

# 3. Run the validator
python scripts/validation/validate_data_layer.py
```

Expected output (3 OK lines, exit 0):

```text
OK: btc-perp-snapshot.json
OK: eth-perp-snapshot.json
OK: sol-perp-snapshot.json
```

If you see any `FAIL:` line, the validator has detected a schema violation. The output names the file, the JSON-pointer of the offending field, and a human-readable error. Re-read the relevant field in [data-model.md](./data-model.md) and fix the fixture (or, if the schema is wrong, the schema).

## How to validate a new fixture

1. Add a JSON file to `specs/002-data-layer/fixtures/` named `<asset>-<type>-snapshot.json`.
2. Conform it to `contracts/snapshot.schema.json` (use the existing fixtures as a reference).
3. Add the new filename to `FIXTURE_TO_SCHEMA` in `scripts/validation/validate_data_layer.py`.
4. Run the validator. It must print `OK:` for the new fixture.

## How to add a new schema

1. Add a JSON Schema 2020-12 file to `specs/002-data-layer/contracts/`.
2. Reference it from any other schema that needs it via `$ref`.
3. Add the new schema to `FIXTURE_TO_SCHEMA` mapping (or add a new mapping dict if the entity is not a snapshot).
4. Update the `validate_data_layer.py` docstring and the `--help` output if the new entity needs different CLI flags.

## Hard rules to honor in any later spec

These are the rules you cannot relax without amending the constitution or this spec:

- **No live exchange API calls.** The validator runs offline. P1 ships fixtures; P2 may add a data ingestion layer, but it must not bypass the JSON Schema contract.
- **No advisory language** in any artifact that touches alerts, journal, or outcomes. P1 enforces this by the absence of advisory fields in the snapshot schema; the journal field guardrail is P4–P5's responsibility.
- **No `liquidity_suitability` mutation.** P1 fixtures set this to `null`. P2 is the documented owner.
- **No `cadence_seconds` in P1.** P3 is the owner of cadence.
- **No schema drift without versioning.** Any future change to a `*.schema.json` MUST bump `schema_version` in every fixture that conforms to it. P1 ships `schema_version: "0.1.0"`; a breaking change requires `"0.2.0"`.
- **No external runtime deps beyond `jsonschema`.** If a future spec needs more, it MUST justify the addition in its own `plan.md` and bump this constraint explicitly.

## How to verify this spec is in good shape

You can sanity-check this spec from a clean clone in under a minute:

```bash
# 1. The spec exists and is not empty
test -s specs/002-data-layer/spec.md && echo OK

# 2. The clarifications are recorded
grep -q "Session 2026-06-21" specs/002-data-layer/spec.md && echo OK

# 3. The plan references the P0 handoff
grep -q "spec-001" specs/002-data-layer/plan.md && echo OK

# 4. The data model is reachable
test -s specs/002-data-layer/data-model.md && echo OK

# 5. The schemas are reachable
test -s specs/002-data-layer/contracts/snapshot.schema.json && echo OK
test -s specs/002-data-layer/contracts/watchlist-asset.schema.json && echo OK
test -s specs/002-data-layer/contracts/trading-universe.schema.json && echo OK

# 6. The fixtures are reachable
test -s specs/002-data-layer/fixtures/btc-perp-snapshot.json && echo OK
test -s specs/002-data-layer/fixtures/eth-perp-snapshot.json && echo OK
test -s specs/002-data-layer/fixtures/sol-perp-snapshot.json && echo OK

# 7. The validator script is present
test -s scripts/validation/validate_data_layer.py && echo OK

# 8. The validator runs and prints 3 OK lines
python scripts/validation/validate_data_layer.py | grep -c "^OK:" | grep -q "^3$" && echo OK
```

If all 8 self-checks print `OK`, the spec is internally consistent and the data layer is ready for P2.

## Validation Evidence (recorded 2026-06-21, pre-merge)

| Check | Observed |
|---|---|
| Self-checks above | 8/8 OK |
| `python scripts/validation/validate_data_layer.py` | 3 OK lines, exit 0 |
| Deliberate violation tests | All 3 violations (missing field, wrong enum, missing timeframe key) caught with named errors and exit 1 |
| Real `[NEEDS CLARIFICATION]` markers in `specs/002-data-layer/` | 0 |
| Tasks in `specs/002-data-layer/tasks.md` | (tracked in tasks.md) |
| Constitution principles in `spec-001/constitution.md` | 7 (I–VII) |
| Constitution check items in `plan.md` | 7, all marked addressed |
| External runtime dependencies | 1 (`jsonschema` 4.x via `uv`) |
| Secrets / live URLs in any P1 artifact | 0 (grep verified) |

### Secret / live-URL scan

```bash
grep -RIn 'sk-\|api_key\|secret\|live\.' specs/002-data-layer/ scripts/validation/ pyproject.toml
# expected: no matches
```

Result: 0 matches.

### Need-clarification scan

```bash
grep -rE '^\[NEEDS CLARIFICATION\]| - \[NEEDS CLARIFICATION\]' \
    specs/002-data-layer/spec.md \
    specs/002-data-layer/plan.md \
    specs/002-data-layer/data-model.md \
    specs/002-data-layer/research.md
# expected: no matches
```

Result: 0 matches.

## Where to ask questions

Open an issue. Use the spec number and the entity or section you are asking about. Examples:

- `[spec-002][data-model] Should `regime` be a per-timeframe field rather than per-snapshot?`
- `[spec-002][fixtures] Is BTC around 64k plausible as a frozen fixture, or should we use round numbers?`
- `[spec-002][scope] Can P2 introduce a venue identifier not in the P1 enum (e.g., `htx`, `kucoin`)?`

Any change that touches a constitutional principle, relaxes a hard rule above, or requires a new external dependency requires an explicit plan update plus a `schema_version` bump.

## Next spec (P2: Scoring Engine)

When P1 is merged, the only allowed handoff is **P2: Scoring Engine v1**. P2 will:

- Consume these three fixtures as test inputs.
- Reference the `MarketContextSnapshot` schema as the contract for any scoring output that includes a snapshot.
- Own regime classification (P1's `unknown` values become real classifications).
- Own `liquidity_suitability` computation (P1's `null` values become real measurements).
- NOT modify any P1 artifact without an amendment.
