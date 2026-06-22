# Quickstart: Scoring Engine v1 (P2)

**Date**: 2026-06-21 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data Model**: [data-model.md](./data-model.md) | **Research**: [research.md](./research.md)

This quickstart is for anyone (you, two months from now, a future agent session) wanting to reproduce the scoring engine from a clean clone. Read it before opening the next spec against this domain.

## What this feature is

This is the **scoring engine** for crypto-alpha. It consumes a `MarketContextSnapshot` from the P1 data layer and produces a `ScoringOutput` containing a decomposable `ConfidenceScore` and an optional `RiskPlan`. The engine is a rules-based, deterministic, auditable function. It is the first spec that interprets market data (P1 only modeled the data shape).

If you are looking for signals, alerts, manual trade journal, outcomes, or learning, you are in the wrong place. Check [plan.md](./plan.md) for the roadmap to P3.

## What to read, in order

1. [`../../.specify/memory/constitution.md`](../../.specify/memory/constitution.md) — the principles this spec is constrained by.
2. [spec.md](./spec.md) — the feature specification, including the 18 clarifications resolved on 2026-06-21.
3. [plan.md](./plan.md) — the technical context, constitution check, and project structure.
4. [research.md](./research.md) — the "why this shape" reasoning for every design decision.
5. [data-model.md](./data-model.md) — the field-level precision for the three output schemas.
6. [checklists/requirements.md](./checklists/requirements.md) — the spec quality gate.
7. `contracts/*.schema.json` — the authoritative machine-readable forms.
8. `fixtures/*.json` — the deterministic sample outputs derived from P1 fixtures.

## How to reproduce scoring from a clean clone

Requires Python 3.11+ (or `uv` to manage it) and ~30 seconds.

```bash
# 1. Clone (or cd into an existing clone)
cd /workspace/crypto-alpha
git checkout 003-scoring-engine-v1

# 2. Create venv and install runtime + dev deps
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 3. Run the test suite (70 tests, includes property-based)
pytest
# expected: 70 passed

# 4. Score the 3 P1 fixtures
python scripts/scoring/score.py score \
  specs/002-data-layer/fixtures/btc-perp-snapshot.json \
  specs/003-scoring-engine-v1/fixtures/btc-scored.json
python scripts/scoring/score.py score \
  specs/002-data-layer/fixtures/eth-perp-snapshot.json \
  specs/003-scoring-engine-v1/fixtures/eth-scored.json
python scripts/scoring/score.py score \
  specs/002-data-layer/fixtures/sol-perp-snapshot.json \
  specs/003-scoring-engine-v1/fixtures/sol-scored.json

# 5. Validate the scored outputs against the output schemas
python scripts/validation/validate_scoring.py
# expected: 3 OK lines, exit 0
```

Expected outcomes:
- **pytest**: 70/70 pass.
- **btc-scored.json**: total_score ≈ 78 (medium), risk_plan emitted (long).
- **eth-scored.json**: total_score ≈ 72 (medium), risk_plan emitted (long).
- **sol-scored.json**: total_score = 0, risk_plan = null, rejection_reason mentions `extreme_volatility`.

## How to score a new snapshot

1. Add a new snapshot JSON to `specs/002-data-layer/fixtures/` (or any path).
2. Score it:
   ```bash
   python scripts/scoring/score.py score <snapshot.json> <output.json>
   ```
3. Validate the output:
   ```bash
   python scripts/validation/validate_scoring.py <output.json>
   ```

## Hard rules to honor in any later spec

These are the rules you cannot relax without amending the constitution or this spec:

- **No live exchange API calls.** The scorer is a pure function on a snapshot. P2 ships fixtures; P3 may add a data ingestion layer, but it must not bypass the snapshot schema.
- **No advisory language** in any artifact that touches alerts, journal, or outcomes. The scorer never produces buy/sell/hold language; only structured confidence and risk plan.
- **No silent rule changes.** Any change to the scoring rules table MUST create `StrategyVersion` v0.2.0; v0.1.0 fixtures remain valid.
- **No opaque confidence.** Every `ConfidenceScore` is a structure. `total_score` is derived, not stored. `components[]` is non-empty and explicitly named.
- **No `float` in money fields.** Decimal strings only. The `to_decimal_string` helper is the single source of truth.
- **No new external runtime deps beyond NumPy, pytest, hypothesis.** If a future spec needs more, it MUST justify the addition in its own `plan.md` and bump this constraint explicitly.
- **No ML.** P2 is rules-based with hand-tuned thresholds. ML-based scoring is a future spec, gated by a calibration spec (P6) and a dedicated review.

## How to verify this spec is in good shape

You can sanity-check this spec from a clean clone in under a minute:

```bash
# 1. The spec exists and is not empty
test -s specs/003-scoring-engine-v1/spec.md && echo OK

# 2. The clarifications are recorded
grep -q "Session 2026-06-21" specs/003-scoring-engine-v1/spec.md && echo OK

# 3. The plan references the P1 handoff
grep -q "specs/002-data-layer/plan.md" specs/003-scoring-engine-v1/plan.md && echo OK

# 4. The data model is reachable
test -s specs/003-scoring-engine-v1/data-model.md && echo OK

# 5. The schemas are reachable
test -s specs/003-scoring-engine-v1/contracts/scoring-output.schema.json && echo OK
test -s specs/003-scoring-engine-v1/contracts/confidence-score.schema.json && echo OK
test -s specs/003-scoring-engine-v1/contracts/risk-plan.schema.json && echo OK

# 6. The scored fixtures are reachable
test -s specs/003-scoring-engine-v1/fixtures/btc-scored.json && echo OK
test -s specs/003-scoring-engine-v1/fixtures/eth-scored.json && echo OK
test -s specs/003-scoring-engine-v1/fixtures/sol-scored.json && echo OK

# 7. The scorer is present
test -s scripts/scoring/score.py && echo OK

# 8. The validator passes
python scripts/validation/validate_scoring.py | grep -c "^OK:" | grep -q "^3$" && echo OK
```

If all 8 self-checks print `OK`, the spec is internally consistent and the scoring engine is ready for P3.

## Validation Evidence (recorded 2026-06-21, pre-merge)

| Check | Observed |
|---|---|
| Self-checks above | 8/8 OK |
| `pytest` | 70/70 pass |
| P2 validator | 3/3 OK (btc, eth, sol) |
| P1 validator (regression) | 3/3 OK (no regression) |
| Real `[NEEDS CLARIFICATION]` markers in `specs/003-scoring-engine-v1/` | 0 |
| Tasks in `specs/003-scoring-engine-v1/tasks.md` | 0 open, all `[X]` |
| Constitution principles in `spec-001/constitution.md` | 7 (I–VII) |
| Constitution check items in `plan.md` | 7, all marked addressed |
| External runtime dependencies | 3 (`numpy`, `pytest`, `hypothesis`); `jsonschema` inherited from P1 |
| Secrets / live URLs in any P2 artifact | 0 |

### Targeted secret / live-URL scan

```bash
grep -RInE 'sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|api[_-]?key[ ]*=[ ]*"[A-Za-z0-9]{16,}"' specs/003-scoring-engine-v1/ scripts/scoring/ scripts/validation/ pyproject.toml
# expected: no matches
```

Result: 0 matches.

### Determinism check

The scorer is a pure function. Given the same snapshot input, it produces byte-identical output. To verify:

```bash
python scripts/scoring/score.py score specs/002-data-layer/fixtures/btc-perp-snapshot.json /tmp/run1.json
python scripts/scoring/score.py score specs/002-data-layer/fixtures/btc-perp-snapshot.json /tmp/run2.json
diff /tmp/run1.json /tmp/run2.json
# expected: no output
```

(Note: `scored_at` is parameterized to a fixed value when the function is called directly via `score_snapshot(snap, ref, scored_at=...)`. The CLI uses a fixed timestamp, so the output is stable across runs.)

## Where to ask questions

Open an issue. Use the spec number and the entity or section you are asking about. Examples:

- `[spec-003][confluence] Why are the three components weighted 0.40/0.30/0.30?`
- `[spec-003][risk-plan] Should the TP ladder include a 4R runner level?`
- `[spec-003][regime] The choppy threshold of 0.85 — is that tunable?`

Any change that touches a constitutional principle, relaxes a hard rule above, or requires a new external dependency requires an explicit plan update plus a `StrategyVersion` bump.

## Next spec (P3: Signal Generator + Alert Format)

When P2 is merged, the only allowed handoff is **P3: Signal Generator + Alert Format**. P3 will:

- Consume the `ScoringOutput` fixtures as test inputs.
- Reference the `ConfidenceScore` and `RiskPlan` schemas as contracts.
- Add the `Signal` entity and the alert rendering.
- NOT modify any P2 artifact without an amendment.
