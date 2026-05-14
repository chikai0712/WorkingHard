#!/usr/bin/env python3
import json
import os
from pathlib import Path

service = os.getenv("SERVICE_NAME", "example-service")
window = os.getenv("TIME_WINDOW", "24h")
script_dir = Path(__file__).resolve().parent

summary = {
    "service": service,
    "window": window,
    "sections": [
        "availability_summary",
        "alert_volume",
        "top_errors",
        "capacity_signals",
        "recommended_followups",
    ],
    "templates": {
        "incident_summary": str(script_dir / "incident-summary.example.json"),
        "metric_snapshot": str(script_dir / "metric-snapshot.example.json"),
        "dashboard_metadata": str(script_dir / "dashboard-metadata.example.yaml"),
        "weekly_ops_review": str(script_dir / "examples" / "weekly-ops-review.md"),
    },
}

print(json.dumps(summary, indent=2))
