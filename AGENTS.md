<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan.

## Current spec status

- **Spec 001** (`001-profitable-trading-decision-domain`): merged (PR #1). The
  foundational product domain. Read `.specify/memory/constitution.md` and
  `specs/001-profitable-trading-decision-domain/spec.md` first.
- **Spec 002** (`002-data-layer`): merged (PR #3). The P0→P1 handoff
  delivering JSON Schemas, multi-asset fixtures, and the local validator.
  Read `specs/002-data-layer/plan.md`. The local validator at
  `scripts/validation/validate_data_layer.py` is the test surface; run it
  with `python scripts/validation/validate_data_layer.py` after
  `uv venv --python 3.11 .venv && source .venv/bin/activate && uv pip install -e .`.
- **Next spec**: P2 (Scoring Engine v1) — branch not yet opened. Will
  consume the P1 fixtures as test inputs and reference the
  `MarketContextSnapshot` schema as the contract for scoring output.
<!-- SPECKIT END -->
