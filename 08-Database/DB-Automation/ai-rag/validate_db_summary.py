#!/usr/bin/env python3
"""Validate DB summary and evidence example artifacts against local JSON schemas.

This validator intentionally implements only the small subset of JSON Schema
features used by the local skeleton files, so it can run without external
packages.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_BINDINGS = {
    "db-backup-summary.example.json": "db-backup-summary.schema.json",
    "db-backup-summary.mysql.example.json": "db-backup-summary.schema.json",
    "db-migration-summary.example.json": "db-migration-summary.schema.json",
    "db-migration-summary.mysql.example.json": "db-migration-summary.schema.json",
    "db-monitoring-summary.example.json": "db-monitoring-summary.schema.json",
    "db-remediation-summary.example.json": "db-remediation-summary.schema.json",
    "db-ansible-summary.example.json": "db-ansible-summary.schema.json",
    "db-mysql-restore-evidence.example.json": "db-mysql-restore-evidence.schema.json",
    "db-mysql-precheck-evidence.example.json": "db-mysql-precheck-evidence.schema.json",
    "db-mysql-postcheck-evidence.example.json": "db-mysql-postcheck-evidence.schema.json",
    "db-monitoring-evidence.example.json": "db-monitoring-evidence.schema.json",
    "db-ansible-evidence.example.json": "db-ansible-evidence.schema.json",
}


def type_matches(expected_type: str, value: Any) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return True


def validate_type(type_spec: str | list[str], value: Any, path: str, errors: list[str]) -> None:
    allowed_types = type_spec if isinstance(type_spec, list) else [type_spec]
    if not any(type_matches(expected_type, value) for expected_type in allowed_types):
        errors.append(f"{path}: expected type {allowed_types}, got {type(value).__name__}")


def validate_schema(schema: dict[str, Any], payload: Any, path: str, errors: list[str]) -> None:
    if "const" in schema and payload != schema["const"]:
        errors.append(f"{path}: expected const value {schema['const']!r}, got {payload!r}")

    if "enum" in schema and payload not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']}, got {payload!r}")

    if "type" in schema:
        validate_type(schema["type"], payload, path, errors)

    schema_type = schema.get("type")
    is_object = schema_type == "object" or (isinstance(schema_type, list) and "object" in schema_type)
    is_array = schema_type == "array" or (isinstance(schema_type, list) and "array" in schema_type)

    if is_object and isinstance(payload, dict):
        for field in schema.get("required", []):
            if field not in payload:
                errors.append(f"{path}: missing required field {field}")

        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            if field_name in payload:
                validate_schema(field_schema, payload[field_name], f"{path}.{field_name}", errors)

    if is_array and isinstance(payload, list) and "items" in schema:
        for index, item in enumerate(payload):
            validate_schema(schema["items"], item, f"{path}[{index}]", errors)


def main() -> None:
    errors: list[str] = []
    for example_name, schema_name in SCHEMA_BINDINGS.items():
        example_path = BASE_DIR / example_name
        schema_path = BASE_DIR / schema_name
        payload = json.loads(example_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validate_schema(schema, payload, example_name, errors)

    if errors:
        print("DB artifact schema validation failed")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"Validated {len(SCHEMA_BINDINGS)} DB summary/evidence artifacts against schema subset")


if __name__ == "__main__":
    main()
