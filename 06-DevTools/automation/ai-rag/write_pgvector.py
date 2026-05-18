#!/usr/bin/env python3
"""Emit pgvector-style records from embedded examples.

This skeleton prepares JSON rows that could later be inserted into PostgreSQL
with pgvector, but does not connect to a real database.
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "examples" / "embedded-records.example.json"
OUTPUT_FILE = BASE_DIR / "examples" / "pgvector-rows.example.json"


def main() -> None:
    records = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    rows = []
    for record in records:
        rows.append(
            {
                "doc_id": record["doc_id"],
                "chunk_id": record["chunk_id"],
                "project": record["project"],
                "module": record["module"],
                "sensitivity": record["sensitivity"],
                "text": record["text"],
                "embedding": record["embedding"],
            }
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(rows)} pgvector-style rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
