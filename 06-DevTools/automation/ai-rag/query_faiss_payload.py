#!/usr/bin/env python3
"""Query FAISS-style payload examples with placeholder similarity.

This skeleton reads local FAISS payload JSON and returns top references using
simple keyword overlap as a stand-in for vector similarity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "examples" / "faiss-payload.example.json"
CHUNK_FILE = BASE_DIR / "examples" / "chunked-records.example.json"
TOP_K = 5


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in text.replace("/", " ").replace("-", " ").replace("_", " ").split() if token}


def similarity(query: str, text: str) -> float:
    query_tokens = tokenize(query)
    text_tokens = tokenize(text)
    if not query_tokens or not text_tokens:
        return 0.0
    overlap = len(query_tokens & text_tokens)
    return round(overlap / len(query_tokens), 4)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query FAISS-style payload references")
    parser.add_argument("query", nargs="+", help="Query text")
    parser.add_argument("--top-k", type=int, default=TOP_K, help="Number of references to return")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    query = " ".join(args.query)
    payload = json.loads(INPUT_FILE.read_text(encoding="utf-8")) if INPUT_FILE.exists() else {"references": []}
    chunks = json.loads(CHUNK_FILE.read_text(encoding="utf-8")) if CHUNK_FILE.exists() else []
    chunk_map = {chunk.get("chunk_id"): chunk for chunk in chunks}

    ranked = []
    for reference in payload.get("references", []):
        chunk = chunk_map.get(reference.get("chunk_id"), {})
        text = chunk.get("text", "")
        score = similarity(query, text)
        if score > 0:
            ranked.append({"score": score, **reference, "text": text})

    ranked.sort(key=lambda item: item["score"], reverse=True)
    print(json.dumps(ranked[: args.top_k], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
