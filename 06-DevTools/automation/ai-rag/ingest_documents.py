#!/usr/bin/env python3
"""Minimal ingestion skeleton for platform AI / RAG datasets.

This script intentionally does not call real embedding providers or vector stores.
It normalizes local files into structured records for later chunking and indexing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES_DIR = Path(__file__).resolve().parent / "examples"
DEFAULT_OUTPUT = EXAMPLES_DIR / "normalized-records.example.json"


def discover_markdown_files(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in paths:
        files.extend(WORKSPACE_ROOT.glob(pattern))
    return sorted({file for file in files if file.is_file()})


def classify_project(relative_path: str) -> str:
    return relative_path.split("/")[0] if "/" in relative_path else "root"


def build_record(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    relative_path = path.relative_to(WORKSPACE_ROOT).as_posix()
    return {
        "doc_id": relative_path.replace("/", "--"),
        "path": relative_path,
        "source_type": "document",
        "project": classify_project(relative_path),
        "module": path.parent.name,
        "sensitivity": "internal",
        "chunk_strategy": "heading-based",
        "content_preview": text[:500],
        "char_count": len(text),
        "status": "normalized",
    }


def normalize_documents(patterns: Iterable[str]) -> list[dict]:
    return [build_record(path) for path in discover_markdown_files(patterns)]


def main() -> None:
    patterns = [
        "06-DevTools/automation/**/*.md",
        "08-Database/DB-Automation/**/*.md",
    ]
    records = normalize_documents(patterns)
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} normalized records to {DEFAULT_OUTPUT}")


if __name__ == "__main__":
    main()
