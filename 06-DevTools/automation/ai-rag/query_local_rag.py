#!/usr/bin/env python3
"""Query the local AI / RAG skeleton outputs.

This retriever scores chunk text by keyword overlap and prefers the scanned DB
artifact dataset when present, falling back to the static example datasets.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CHUNK_FILE = BASE_DIR / "examples" / "chunked-records.example.json"
DB_DATASET_FILE = BASE_DIR.parents[2] / "08-Database/DB-Automation/ai-rag/db-summary-dataset.example.json"
DB_DATASET_WITH_EVIDENCE_FILE = BASE_DIR.parents[2] / "08-Database/DB-Automation/ai-rag/db-summary-dataset.with-evidence.example.json"
DB_LATEST_SCOPED_DATASET_FILE = BASE_DIR.parents[2] / "08-Database/DB-Automation/ai-rag/db-summary-dataset.latest-scoped.example.json"
DB_SCANNED_DATASET_FILE = BASE_DIR.parents[2] / "08-Database/DB-Automation/ai-rag/db-summary-dataset.scanned.example.json"
TOP_K = 5


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in text.replace("/", " ").replace("-", " ").replace("_", " ").split() if token}


def score(query: str, text: str) -> int:
    return len(tokenize(query) & tokenize(text))


def payload_to_text(payload: dict) -> str:
    parts: list[str] = []
    for key in (
        "summary",
        "status",
        "severity",
        "risk_level",
        "module",
        "alert_name",
        "device_family",
        "backup_type",
        "stage",
        "evidence_type",
        "restore_target",
    ):
        value = payload.get(key)
        if isinstance(value, str):
            parts.append(value)

    for key in (
        "recommended_checks",
        "possible_causes",
        "rollback_reference",
        "affected_targets",
        "affected_devices",
        "evidence",
    ):
        value = payload.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)

    for key in ("checks", "observations"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    parts.extend(str(subvalue) for subvalue in item.values())

    binlog_validation = payload.get("binlog_validation")
    if isinstance(binlog_validation, dict):
        parts.extend(str(value) for value in binlog_validation.values())

    return " ".join(parts)


def load_dataset(dataset_file: Path) -> list[dict]:
    return json.loads(dataset_file.read_text(encoding="utf-8")) if dataset_file.exists() else []


def normalize_record(item: dict, dataset_file: Path) -> dict:
    payload = item.get("summary", {})
    return {
        "chunk_id": item.get("event_id", "unknown"),
        "doc_id": item.get("module", "unknown"),
        "path": item.get("source_file", dataset_file.name),
        "record_type": item.get("record_type", "summary"),
        "schema_file": item.get("schema_file"),
        "text": payload_to_text(payload),
        "summary": payload.get("summary", ""),
    }


def load_records(include_evidence: bool, scoped_only: bool) -> list[dict]:
    records = [] if scoped_only else (json.loads(CHUNK_FILE.read_text(encoding="utf-8")) if CHUNK_FILE.exists() else [])
    if DB_LATEST_SCOPED_DATASET_FILE.exists():
        dataset_file = DB_LATEST_SCOPED_DATASET_FILE
    elif DB_SCANNED_DATASET_FILE.exists():
        dataset_file = DB_SCANNED_DATASET_FILE
    else:
        dataset_file = DB_DATASET_WITH_EVIDENCE_FILE if include_evidence else DB_DATASET_FILE
    summaries = load_dataset(dataset_file)
    if include_evidence and dataset_file == DB_DATASET_FILE and DB_DATASET_WITH_EVIDENCE_FILE.exists():
        summaries = load_dataset(DB_DATASET_WITH_EVIDENCE_FILE)

    for item in summaries:
        if not include_evidence and item.get("record_type") == "evidence":
            continue
        records.append(normalize_record(item, dataset_file))
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query local AI / RAG skeleton records")
    parser.add_argument("query", nargs="+", help="Query text")
    parser.add_argument(
        "--include-evidence",
        action="store_true",
        help="Search the DB dataset that includes evidence records",
    )
    parser.add_argument(
        "--scoped-only",
        action="store_true",
        help="Only search the latest scoped/scanned dataset and skip chunk/example fallback records",
    )
    parser.add_argument("--top-k", type=int, default=TOP_K, help="Number of results to return")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    query = " ".join(args.query).strip()
    if not query:
        raise SystemExit("Usage: query_local_rag.py <query>")

    ranked = []
    for record in load_records(include_evidence=args.include_evidence, scoped_only=args.scoped_only):
        relevance = score(query, record.get("text", ""))
        if relevance > 0:
            ranked.append({"score": relevance, **record})

    ranked.sort(key=lambda item: item["score"], reverse=True)
    print(json.dumps(ranked[: args.top_k], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
