#!/usr/bin/env python3
"""Emit FAISS-style payload examples from embedded records.

This skeleton prepares a flat list of vectors and metadata references for later
FAISS indexing, but does not build a real FAISS index yet.
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "examples" / "embedded-records.example.json"
OUTPUT_FILE = BASE_DIR / "examples" / "faiss-payload.example.json"


def main() -> None:
    records = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    payload = {
        "vectors": [record["embedding"] for record in records],
        "references": [
            {
                "doc_id": record["doc_id"],
                "chunk_id": record["chunk_id"],
                "path": record["path"],
            }
            for record in records
        ],
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote FAISS-style payload to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
