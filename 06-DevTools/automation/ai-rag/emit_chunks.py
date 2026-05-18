#!/usr/bin/env python3
"""Emit chunked records from sanitized AI / RAG records.

The chunker is intentionally simple: fixed-size character windows with overlap.
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "examples" / "sanitized-records.example.json"
OUTPUT_FILE = BASE_DIR / "examples" / "chunked-records.example.json"
CHUNK_SIZE = 1200
OVERLAP = 200


def chunk_text(text: str) -> list[str]:
    if len(text) <= CHUNK_SIZE:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - OVERLAP, start + 1)
    return chunks


def emit_chunks(records: list[dict]) -> list[dict]:
    emitted: list[dict] = []
    for record in records:
        preview = record.get("content_preview", "")
        for index, chunk in enumerate(chunk_text(preview)):
            emitted.append(
                {
                    "chunk_id": f"{record['doc_id']}::chunk-{index}",
                    "doc_id": record["doc_id"],
                    "path": record["path"],
                    "project": record["project"],
                    "module": record["module"],
                    "sensitivity": record["sensitivity"],
                    "text": chunk,
                }
            )
    return emitted


def main() -> None:
    records = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    chunks = emit_chunks(records)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(chunks)} chunks to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
