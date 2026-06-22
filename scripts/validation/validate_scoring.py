#!/usr/bin/env python3
"""
crypto-alpha P2 Scoring Engine Validator.

Validates that every scored fixture under specs/003-scoring-engine-v1/fixtures/
conforms to the corresponding JSON Schema under specs/003-scoring-engine-v1/contracts/.

Local, offline, deterministic. Same exit-code semantics as the P1 validator
(0 = success, 1 = validation failure, 2 = setup error).

Usage:
    python scripts/validation/validate_scoring.py
    python scripts/validation/validate_scoring.py --fixtures-dir <path> --contracts-dir <path>
    python scripts/validation/validate_scoring.py <scored.json>  # validate a single file
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "ERROR: jsonschema is not installed. Run: uv pip install jsonschema\n"
    )
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES_DIR = REPO_ROOT / "specs" / "003-scoring-engine-v1" / "fixtures"
DEFAULT_CONTRACTS_DIR = REPO_ROOT / "specs" / "003-scoring-engine-v1" / "contracts"
DEFAULT_SCORING_OUTPUT_SCHEMA = "scoring-output.schema.json"
FIXTURE_TO_SCHEMA: dict[str, str] = {
    "btc-scored.json": "scoring-output.schema.json",
    "eth-scored.json": "scoring-output.schema.json",
    "sol-scored.json": "scoring-output.schema.json",
}


def _format_error_path(error: jsonschema.ValidationError) -> str:
    parts: list[str] = []
    for token in error.absolute_path:
        if isinstance(token, int):
            parts.append(f"[{token}]")
        else:
            parts.append(f".{token}" if parts else token)
    return "".join(parts) or "<root>"


def _format_error(error: jsonschema.ValidationError) -> str:
    path = _format_error_path(error)
    message = error.message
    if error.validator == "enum":
        allowed = ", ".join(repr(v) for v in (error.validator_value or []))
        message = f"{message} (allowed: {allowed})"
    return f"{path}: {message}"


def _load_schema(contracts_dir: Path, schema_name: str, schema_cache: dict[str, dict]) -> dict:
    if schema_name in schema_cache:
        return schema_cache[schema_name]
    schema_path = contracts_dir / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    schema_cache[schema_name] = schema
    return schema


def _load_ref_schema(contracts_dir: Path, ref_path: str, schema_cache: dict[str, dict]) -> dict:
    """Resolve a relative $ref (e.g. confidence-score.schema.json)."""
    return _load_schema(contracts_dir, ref_path, schema_cache)


def _build_validator(
    contracts_dir: Path,
    schema_name: str,
    schema_cache: dict[str, dict],
) -> Draft202012Validator:
    schema = _load_schema(contracts_dir, schema_name, schema_cache)
    # Pre-resolve any local $ref to sibling files.
    resolver = jsonschema.RefResolver(
        base_uri=schema.get("$id", ""),
        referrer=schema,
        store=schema_cache,
    )
    # Populate the cache with referenced sibling schemas.
    for ref in ("confidence-score.schema.json", "risk-plan.schema.json"):
        ref_path = contracts_dir / ref
        if ref_path.exists() and ref not in schema_cache:
            with ref_path.open("r", encoding="utf-8") as f:
                schema_cache[ref] = json.load(f)
    return Draft202012Validator(schema, resolver=resolver)


def validate_file(fixture_path: Path, contracts_dir: Path = DEFAULT_CONTRACTS_DIR) -> int:
    if not fixture_path.exists():
        sys.stderr.write(f"ERROR: fixture not found: {fixture_path}\n")
        return 2
    schema_name = FIXTURE_TO_SCHEMA.get(fixture_path.name, DEFAULT_SCORING_OUTPUT_SCHEMA)
    schema_cache: dict[str, dict] = {}
    try:
        validator = _build_validator(contracts_dir, schema_name, schema_cache)
    except (FileNotFoundError, jsonschema.SchemaError) as exc:
        sys.stderr.write(f"ERROR: could not build validator: {exc}\n")
        return 2
    with fixture_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        sys.stderr.write(f"FAIL: {fixture_path.name}\n")
        for err in errors:
            sys.stderr.write(f"  - {_format_error(err)}\n")
        return 1
    print(f"OK: {fixture_path.name}")
    return 0


def validate_dir(
    fixtures_dir: Path = DEFAULT_FIXTURES_DIR,
    contracts_dir: Path = DEFAULT_CONTRACTS_DIR,
) -> int:
    if not fixtures_dir.exists():
        sys.stderr.write(f"ERROR: fixtures directory not found: {fixtures_dir}\n")
        return 2
    fixture_paths = sorted(fixtures_dir.glob("*.json"))
    if not fixture_paths:
        sys.stderr.write(f"ERROR: no fixtures found in {fixtures_dir}\n")
        return 2
    exit_code = 0
    for fp in fixture_paths:
        code = validate_file(fp, contracts_dir)
        exit_code = exit_code or code
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate crypto-alpha P2 scoring engine fixtures against JSON Schemas."
    )
    parser.add_argument(
        "fixture",
        nargs="?",
        type=Path,
        default=None,
        help="Optional path to a single fixture JSON. If omitted, validates all fixtures in the default dir.",
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=DEFAULT_FIXTURES_DIR,
    )
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=DEFAULT_CONTRACTS_DIR,
    )
    args = parser.parse_args(argv)
    if args.fixture is not None:
        return validate_file(args.fixture, args.contracts_dir)
    return validate_dir(args.fixtures_dir, args.contracts_dir)


if __name__ == "__main__":
    raise SystemExit(main())
