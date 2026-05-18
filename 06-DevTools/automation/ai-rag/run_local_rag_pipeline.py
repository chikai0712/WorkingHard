#!/usr/bin/env python3
"""Run the local AI / RAG skeleton pipeline end-to-end.

Pipeline:
1. ingest_documents.py
2. sanitize_records.py
3. validate_metadata.py
4. emit_chunks.py
5. embed_records.py
6. write_pgvector.py
7. write_faiss.py
8. validate_db_summary.py
9. ingest_db_summaries.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_AI_RAG_DIR = BASE_DIR.parents[2] / "08-Database/DB-Automation/ai-rag"
PIPELINE_STEPS = [
    (BASE_DIR, "ingest_documents.py"),
    (BASE_DIR, "sanitize_records.py"),
    (BASE_DIR, "validate_metadata.py"),
    (BASE_DIR, "emit_chunks.py"),
    (BASE_DIR, "embed_records.py"),
    (BASE_DIR, "write_pgvector.py"),
    (BASE_DIR, "write_faiss.py"),
    (DB_AI_RAG_DIR, "validate_db_summary.py"),
    (DB_AI_RAG_DIR, "ingest_db_summaries.py"),
]


def run_step(script_dir: Path, script_name: str) -> None:
    script_path = script_dir / script_name
    print(f"[pipeline] running {script_name}")
    subprocess.run([sys.executable, str(script_path)], check=True, cwd=str(script_dir))


def main() -> None:
    for script_dir, script_name in PIPELINE_STEPS:
        run_step(script_dir, script_name)
    print("[pipeline] local AI / RAG skeleton pipeline complete")


if __name__ == "__main__":
    main()
