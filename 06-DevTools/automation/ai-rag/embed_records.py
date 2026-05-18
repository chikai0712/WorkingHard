#!/usr/bin/env python3
"""Generate placeholder embeddings from chunked records.

This skeleton does not call a real embedding provider. It emits deterministic
placeholder vectors so downstream vector-store writers can be tested safely.
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "examples" / "chunked-records.example.json"
OUTPUT_FILE = BASE_DIR / "examples" / "embedded-records.example.json"
VECTOR_SIZE = 8


def placeholder_embedding(text: str) -> list[float]:
    seed = sum(ord(char) for char in text) % 997
    return [round(((seed + index * 37) % 100) / 100, 4) for index in range(VECTOR_SIZE)]


def main() -> None:
    records = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    embedded = []
    for record in records:
        embedded.append(
            {
                **record,
                "embedding_model": "placeholder-embedding-model",
                "embedding": placeholder_embedding(record.get("text", "")),
            }
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(embedded, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(embedded)} embedded records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
