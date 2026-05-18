#!/usr/bin/env python3
"""Sanitize normalized AI / RAG records.

This skeleton masks obviously sensitive token-like strings and removes empty previews.
It is intentionally conservative and should be extended with project-specific rules.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "examples" / "normalized-records.example.json"
OUTPUT_FILE = BASE_DIR / "examples" / "sanitized-records.example.json"
TOKEN_PATTERN = re.compile(r"(?i)(token|password|secret|apikey|api_key)\s*[:=]\s*[^\s]+")


def sanitize_text(value: str) -> str:
    return TOKEN_PATTERN.sub(r"\1=[REDACTED]", value)


def sanitize_record(record: dict) -> dict:
    sanitized = dict(record)
    preview = sanitized.get("content_preview", "")
    sanitized["content_preview"] = sanitize_text(preview)
    sanitized["status"] = "sanitized"
    return sanitized


def main() -> None:
    records = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    sanitized = [sanitize_record(record) for record in records]
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(sanitized, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(sanitized)} sanitized records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
