#!/usr/bin/env python3
"""Validate metadata on sanitized AI / RAG records."""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "examples" / "sanitized-records.example.json"
REQUIRED_FIELDS = {
    "doc_id",
    "path",
    "source_type",
    "project",
    "module",
    "sensitivity",
    "chunk_strategy",
    "status",
}


def validate_record(record: dict) -> list[str]:
    missing = sorted(REQUIRED_FIELDS - set(record.keys()))
    return [f"missing field: {field}" for field in missing]


def main() -> None:
    records = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    errors: list[str] = []
    for index, record in enumerate(records):
        for issue in validate_record(record):
            errors.append(f"record[{index}] {issue}")

    if errors:
        print("Metadata validation failed")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"Validated {len(records)} records with required metadata")


if __name__ == "__main__":
    main()
