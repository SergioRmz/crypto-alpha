#!/usr/bin/env python3
"""
crypto-alpha P1 Data Layer Validator.

Validates that every fixture file under specs/002-data-layer/fixtures/
conforms to the corresponding JSON Schema under specs/002-data-layer/contracts/.

This is a local, offline, deterministic validator. It does not call any
network endpoint, exchange API, or live data source. Its only external
runtime dependency is jsonschema 4.x.

Usage:
    python scripts/validation/validate_data_layer.py
    python scripts/validation/validate_data_layer.py --fixtures-dir <path> --contracts-dir <path>
    python scripts/validation/validate_data_layer.py --verbose

Exit codes:
    0  All fixtures valid.
    1  One or more fixtures failed validation.
    2  Setup error (schema not found, fixtures dir missing, etc.).
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


# Default paths (relative to repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES_DIR = REPO_ROOT / "specs" / "002-data-layer" / "fixtures"
DEFAULT_CONTRACTS_DIR = REPO_ROOT / "specs" / "002-data-layer" / "contracts"

# Map fixture filename -> schema filename.
FIXTURE_TO_SCHEMA: dict[str, str] = {
    "btc-perp-snapshot.json": "snapshot.schema.json",
    "eth-perp-snapshot.json": "snapshot.schema.json",
    "sol-perp-snapshot.json": "snapshot.schema.json",
}


def _format_error_path(error: jsonschema.ValidationError) -> str:
    """Render the JSON pointer of a validation error in human-readable form."""
    parts: list[str] = []
    for token in error.absolute_path:
        if isinstance(token, int):
            parts.append(f"[{token}]")
        else:
            parts.append(f".{token}" if parts else token)
    return "".join(parts) or "<root>"


def _format_error(error: jsonschema.ValidationError) -> str:
    """Render a single validation error as a single-line, human-readable string."""
    path = _format_error_path(error)
    message = error.message
    if error.validator == "enum":
        allowed = ", ".join(repr(v) for v in (error.validator_value or []))
        message = f"{message} (allowed: {allowed})"
    elif error.validator == "required":
        # The default message is: "'foo' is a required property"
        message = f"missing required field: {error.message}"
    return f"{path}: {message}"


def _load_schema(contracts_dir: Path, schema_name: str) -> dict[str, Any]:
    schema_path = contracts_dir / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_fixture(fixtures_dir: Path, fixture_name: str) -> dict[str, Any]:
    fixture_path = fixtures_dir / fixture_name
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    with fixture_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _cross_check_universe_cardinality(fixtures_dir: Path) -> list[str]:
    """Optional: ensure (canonical_symbol, venue) pairs are unique across fixtures.

    This is a P1-friendly sanity check; it is not a schema-level constraint.
    """
    errors: list[str] = []
    seen: dict[tuple[str, str], str] = {}
    for fixture_path in sorted(fixtures_dir.glob("*-snapshot.json")):
        try:
            data = _load_fixture(fixtures_dir, fixture_path.name)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            errors.append(f"{fixture_path.name}: could not load for cardinality check: {exc}")
            continue
        key = (data.get("canonical_symbol", ""), data.get("venue", ""))
        if key in seen:
            errors.append(
                f"Duplicate (canonical_symbol, venue) pair {key} in "
                f"{fixture_path.name} and {seen[key]}"
            )
        else:
            seen[key] = fixture_path.name
    return errors


def validate_data_layer(
    fixtures_dir: Path = DEFAULT_FIXTURES_DIR,
    contracts_dir: Path = DEFAULT_CONTRACTS_DIR,
    verbose: bool = False,
) -> int:
    """Run the validation. Returns the process exit code (0 on success)."""
    if not fixtures_dir.exists():
        sys.stderr.write(f"ERROR: fixtures directory not found: {fixtures_dir}\n")
        return 2
    if not contracts_dir.exists():
        sys.stderr.write(f"ERROR: contracts directory not found: {contracts_dir}\n")
        return 2

    # Pre-load every schema we will need.
    schema_cache: dict[str, tuple[dict[str, Any], Draft202012Validator]] = {}
    for schema_name in set(FIXTURE_TO_SCHEMA.values()):
        try:
            schema = _load_schema(contracts_dir, schema_name)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            sys.stderr.write(f"ERROR: could not load schema {schema_name}: {exc}\n")
            return 2
        try:
            validator = Draft202012Validator(schema)
        except jsonschema.SchemaError as exc:
            sys.stderr.write(f"ERROR: schema {schema_name} is not a valid JSON Schema 2020-12: {exc}\n")
            return 2
        schema_cache[schema_name] = (schema, validator)

    fixture_paths = sorted(fixtures_dir.glob("*.json"))
    if not fixture_paths:
        sys.stderr.write(f"ERROR: no fixtures found in {fixtures_dir}\n")
        return 2

    exit_code = 0
    ok_count = 0
    fail_count = 0

    for fixture_path in fixture_paths:
        fixture_name = fixture_path.name
        schema_name = FIXTURE_TO_SCHEMA.get(fixture_name)
        if schema_name is None:
            sys.stderr.write(
                f"SKIP: {fixture_name}: no schema mapping declared in validator\n"
            )
            continue
        if schema_name not in schema_cache:
            sys.stderr.write(f"SKIP: {fixture_name}: schema {schema_name} not loaded\n")
            continue

        try:
            fixture = _load_fixture(fixtures_dir, fixture_name)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            sys.stderr.write(f"FAIL: {fixture_name}: could not load JSON: {exc}\n")
            fail_count += 1
            exit_code = 1
            continue

        _, validator = schema_cache[schema_name]
        errors = sorted(validator.iter_errors(fixture), key=lambda e: list(e.absolute_path))
        if errors:
            sys.stderr.write(f"FAIL: {fixture_name}\n")
            for err in errors:
                sys.stderr.write(f"  - {_format_error(err)}\n")
                if verbose:
                    sys.stderr.write(
                        f"    [validator={err.validator}, schema_path={list(err.absolute_schema_path)}]\n"
                    )
            fail_count += 1
            exit_code = 1
        else:
            print(f"OK: {fixture_name}")
            ok_count += 1

    # Post-schema cross checks.
    cross_errors = _cross_check_universe_cardinality(fixtures_dir)
    if cross_errors:
        sys.stderr.write("FAIL: cross-check errors\n")
        for err in cross_errors:
            sys.stderr.write(f"  - {err}\n")
        exit_code = 1

    if verbose or exit_code != 0:
        print(
            f"Summary: {ok_count} OK, {fail_count} FAIL, "
            f"{len(cross_errors)} cross-check error(s)",
            file=sys.stderr,
        )

    return exit_code


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate crypto-alpha P1 data layer fixtures against JSON Schemas."
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=DEFAULT_FIXTURES_DIR,
        help="Directory containing fixture JSON files.",
    )
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=DEFAULT_CONTRACTS_DIR,
        help="Directory containing JSON Schema files.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print extended diagnostic information for failures.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return validate_data_layer(
        fixtures_dir=args.fixtures_dir,
        contracts_dir=args.contracts_dir,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    raise SystemExit(main())
