#!/usr/bin/env python3
"""Ingest DB summary and optional evidence artifacts into a local dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "db-summary-dataset.example.json"
ARTIFACT_DIR = BASE_DIR / "producer-artifacts"
SUMMARY_FILES = [
    BASE_DIR / "db-backup-summary.example.json",
    BASE_DIR / "db-backup-summary.mysql.example.json",
    BASE_DIR / "db-migration-summary.example.json",
    BASE_DIR / "db-migration-summary.mysql.example.json",
    BASE_DIR / "db-monitoring-summary.example.json",
    BASE_DIR / "db-remediation-summary.example.json",
    BASE_DIR / "db-ansible-summary.example.json",
]
EVIDENCE_FILES = [
    BASE_DIR / "db-mysql-restore-evidence.example.json",
    BASE_DIR / "db-mysql-precheck-evidence.example.json",
    BASE_DIR / "db-mysql-postcheck-evidence.example.json",
    BASE_DIR / "db-monitoring-evidence.example.json",
    BASE_DIR / "db-ansible-evidence.example.json",
]
SUMMARY_SCHEMA_BY_MODULE = {
    "backup-recovery": BASE_DIR / "db-backup-summary.schema.json",
    "migration": BASE_DIR / "db-migration-summary.schema.json",
    "monitoring/k8s": BASE_DIR / "db-monitoring-summary.schema.json",
    "remediation": BASE_DIR / "db-remediation-summary.schema.json",
    "ansible": BASE_DIR / "db-ansible-summary.schema.json",
}
EVIDENCE_SCHEMA_HINTS = {
    ("backup-recovery", "restore-drill"): BASE_DIR / "db-mysql-restore-evidence.schema.json",
    ("migration", "precheck"): BASE_DIR / "db-mysql-precheck-evidence.schema.json",
    ("migration", "postcheck"): BASE_DIR / "db-mysql-postcheck-evidence.schema.json",
    ("monitoring/k8s", "alert-evidence"): BASE_DIR / "db-monitoring-evidence.schema.json",
    ("ansible", "consistency-check"): BASE_DIR / "db-ansible-evidence.schema.json",
}


def build_record(path: Path, record_type: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "source_file": path.name,
        "record_type": record_type,
        "module": payload.get("module"),
        "event_id": payload.get("event_id"),
        "summary": payload,
    }


def infer_record_type(payload: dict) -> str:
    if payload.get("evidence_type"):
        return "evidence"
    return "summary"


def infer_schema_path(payload: dict, record_type: str) -> Path | None:
    if record_type == "summary":
        return SUMMARY_SCHEMA_BY_MODULE.get(payload.get("module"))
    module = payload.get("module")
    evidence_type = payload.get("evidence_type")
    if module == "backup-recovery":
        return EVIDENCE_SCHEMA_HINTS.get((module, evidence_type))
    if module == "migration":
        return EVIDENCE_SCHEMA_HINTS.get((module, payload.get("stage")))
    return EVIDENCE_SCHEMA_HINTS.get((module, evidence_type))


def scan_artifact_dir(scan_dir: Path, scope_prefix: str | None = None) -> list[dict]:
    if not scan_dir.exists():
        return []

    records: list[dict] = []
    for path in sorted(scan_dir.rglob("*.json")):
        relative_parent = str(path.parent.relative_to(scan_dir)) if path.parent != scan_dir else ""
        if scope_prefix and not relative_parent.startswith(scope_prefix):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        record_type = infer_record_type(payload)
        schema_path = infer_schema_path(payload, record_type)
        records.append(
            {
                "source_file": path.name,
                "artifact_scope": relative_parent or "root",
                "session_scope": relative_parent.split("/")[0] if relative_parent else "root",
                "action_scope": relative_parent.split("/")[-1] if relative_parent else "root",
                "record_type": record_type,
                "module": payload.get("module"),
                "event_id": payload.get("event_id"),
                "schema_file": schema_path.name if schema_path else None,
                "summary": payload,
            }
        )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build combined DB summary dataset example")
    parser.add_argument(
        "--include-evidence",
        action="store_true",
        help="Include MySQL evidence example records in the combined dataset",
    )
    parser.add_argument(
        "--scan-dir",
        type=Path,
        default=None,
        help="Scan producer artifact directory and merge discovered JSON records",
    )
    parser.add_argument(
        "--scope-prefix",
        default=None,
        help="Only include scanned records whose artifact scope starts with this prefix",
    )
    parser.add_argument(
        "--scoped-only",
        action="store_true",
        help="Only emit scanned scoped records and skip built-in example dataset records",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_FILE,
        help="Output dataset file path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = [] if args.scoped_only else [build_record(path, "summary") for path in SUMMARY_FILES]

    if args.include_evidence and not args.scoped_only:
        dataset.extend(build_record(path, "evidence") for path in EVIDENCE_FILES)

    scan_dir = args.scan_dir or ARTIFACT_DIR
    scanned_records = scan_artifact_dir(scan_dir, scope_prefix=args.scope_prefix)
    dataset.extend(scanned_records)

    args.output.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote combined DB dataset to {args.output}")
    if not args.scoped_only:
        print(f"Included {len(SUMMARY_FILES)} summary records")
        if args.include_evidence:
            print(f"Included {len(EVIDENCE_FILES)} evidence records")
    if scanned_records:
        print(f"Included {len(scanned_records)} scanned producer records from {scan_dir}")
        if args.scope_prefix:
            print(f"Applied scope prefix filter: {args.scope_prefix}")


if __name__ == "__main__":
    main()
