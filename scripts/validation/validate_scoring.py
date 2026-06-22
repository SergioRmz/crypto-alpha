#!/usr/bin/env python3
"""
crypto-alpha P2 Scoring Engine Validator.

Validates that every scored fixture under specs/003-scoring-engine-v1/fixtures/
conforms to the corresponding JSON Schema under specs/003-scoring-engine-v1/contracts/.

Local, offline, deterministic. Same exit-code semantics as the P1 validator
(0 = success, 1 = validation failure, 2 = setup error).

Usage:
    python scripts/validation/validate_scoring.py
    python scripts/validation/validate_scoring.py <scored.json>  # single file
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Make the `scripts` package importable when running this file directly.
_PKG_PARENT = Path(__file__).resolve().parents[2]
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

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


def _inline_and_strip(node: Any, schema_cache: dict[str, dict], root_defs: dict | None = None) -> None:
    """Recursively inline sibling $refs and strip $id (offline-only)."""
    if root_defs is None and isinstance(node, dict) and "$defs" not in node:
        # First call on the root schema: create its $defs container.
        node.setdefault("$defs", {})

    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and not ref.startswith(("http://", "https://", "file://", "#")):
            if ref in schema_cache:
                inline = json.loads(json.dumps(schema_cache[ref]))
                inline.pop("$id", None)
                # Lift any $defs from the inlined schema up to the
                # root_defs (renamed) so internal #/$defs/... refs
                # resolve from the document root.
                defs = inline.get("$defs")
                target_defs = root_defs if root_defs is not None else node.setdefault("$defs", {})
                if isinstance(defs, dict):
                    for k in list(defs.keys()):
                        new_key = f"{ref.replace('.schema.json', '')}__{k}"
                        target_defs[new_key] = defs[k]

                        def _update(n: Any) -> None:
                            if isinstance(n, dict):
                                r = n.get("$ref")
                                if isinstance(r, str) and r == f"#/$defs/{k}":
                                    n["$ref"] = f"#/$defs/{new_key}"
                                for vv in n.values():
                                    _update(vv)
                            elif isinstance(n, list):
                                for vv in n:
                                    _update(vv)

                        _update(inline)
                inline.pop("$defs", None)
                # Recurse on the inlined content (without lifting further
                # $defs since they would already be at root).
                _inline_and_strip(inline, schema_cache, target_defs)
                node.pop("$ref")
                node.update(inline)
        node.pop("$id", None)
        for v in list(node.values()):
            _inline_and_strip(v, schema_cache, root_defs)
    elif isinstance(node, list):
        for v in node:
            _inline_and_strip(v, schema_cache, root_defs)


def _build_validator(
    contracts_dir: Path,
    schema_name: str,
    schema_cache: dict[str, dict],
) -> Draft202012Validator:
    """Build a validator that resolves sibling $refs entirely offline.

    We inline referenced schemas and lift their $defs to the root so
    internal #/$defs/... refs resolve correctly. All $id fields are
    stripped so the validator never attempts an HTTP fetch.
    """
    schema = _load_schema(contracts_dir, schema_name, schema_cache)
    for sibling in ("confidence-score.schema.json", "risk-plan.schema.json"):
        if sibling != schema_name:
            _load_schema(contracts_dir, sibling, schema_cache)
    # Ensure root has $defs before any inlining starts.
    schema.setdefault("$defs", {})
    _inline_and_strip(schema, schema_cache, schema["$defs"])
    return Draft202012Validator(schema)


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
        help="Optional path to a single fixture JSON.",
    )
    parser.add_argument("--fixtures-dir", type=Path, default=DEFAULT_FIXTURES_DIR)
    parser.add_argument("--contracts-dir", type=Path, default=DEFAULT_CONTRACTS_DIR)
    args = parser.parse_args(argv)
    if args.fixture is not None:
        return validate_file(args.fixture, args.contracts_dir)
    return validate_dir(args.fixtures_dir, args.contracts_dir)


if __name__ == "__main__":
    raise SystemExit(main())
