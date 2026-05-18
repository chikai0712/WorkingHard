#!/usr/bin/env python3
"""Score local retrieval quality against evaluation questions.

This skeleton measures whether any expected source path appears in top-k
retrieval results from `query_local_rag.py`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = BASE_DIR / "evaluation-questions.example.json"
QUERY_SCRIPT = BASE_DIR / "query_local_rag.py"
TOP_K = 5


def run_query(question: str) -> list[dict]:
    result = subprocess.run(
        [sys.executable, str(QUERY_SCRIPT), question],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(BASE_DIR),
    )
    return json.loads(result.stdout or "[]")


def main() -> None:
    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    report = []
    hits = 0
    for item in questions:
        results = run_query(item["question"])
        paths = [result.get("path", "") for result in results[:TOP_K]]
        matched = any(expected in paths for expected in item.get("expected_sources", []))
        hits += int(matched)
        report.append(
            {
                "question": item["question"],
                "matched": matched,
                "top_paths": paths,
            }
        )

    output = {
        "questions": len(questions),
        "matched": hits,
        "score": round(hits / len(questions), 4) if questions else 0,
        "report": report,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
