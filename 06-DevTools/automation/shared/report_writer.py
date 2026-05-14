#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import json


def write_report(output_dir: str, name: str, payload: dict) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    report_path = path / f"{name}-{timestamp}.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return report_path


if __name__ == "__main__":
    result = write_report("./reports", "sample", {"status": "ok"})
    print(result)
