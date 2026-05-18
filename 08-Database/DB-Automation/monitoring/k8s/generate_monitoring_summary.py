#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, UTC
from pathlib import Path

alert_name = os.getenv("ALERT_NAME", "DBExporterTargetsWarning")
severity = os.getenv("SEVERITY", "warning")
summary_out = os.getenv("SUMMARY_OUT", "")
evidence_out = os.getenv("EVIDENCE_OUT", "")
artifact_dir = os.getenv("ARTIFACT_DIR", "")

print(f"[monitoring-summary] alert={alert_name} severity={severity}")
print("[monitoring-summary] Step 1: inspect exporter/Prometheus health placeholders")
print("[monitoring-summary] Step 2: map alert to summary schema")
print("[monitoring-summary] Step 3: no real cluster connection in skeleton mode")

updated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
summary_payload = {
    "event_id": "monitoring-summary-local",
    "module": "monitoring/k8s",
    "alert_name": alert_name,
    "severity": severity,
    "summary": "Monitoring summary generated in skeleton mode; exporter readiness and alert evidence still require operator review.",
    "affected_targets": ["mysql-exporter-01"],
    "recommended_checks": [
        "Review exporter readiness",
        "Confirm Prometheus target health",
        "Check alert rule and dashboard mapping",
    ],
    "recommended_policy": "hold",
    "updated_at": updated_at,
}

evidence_payload = {
    "event_id": "monitoring-evidence-local",
    "module": "monitoring/k8s",
    "evidence_type": "alert-evidence",
    "alert_name": alert_name,
    "status": severity,
    "summary": "Monitoring evidence generated in skeleton mode; target health and alert observations still require operator review.",
    "affected_targets": ["mysql-exporter-01"],
    "observations": [
        {
            "name": "prometheus_target_health",
            "status": "ok",
            "value": "up",
            "notes": "Exporter target is reachable in skeleton mode",
        },
        {
            "name": "alert_rule_state",
            "status": severity,
            "value": "firing",
            "notes": "Placeholder alert remains active for review",
        },
    ],
    "recommended_checks": [
        "Review exporter readiness",
        "Confirm Prometheus target health",
        "Check alert rule and dashboard mapping",
    ],
    "recommended_policy": "hold",
    "updated_at": updated_at,
}

summary_path: Path | None = None
evidence_path: Path | None = None
if summary_out:
    summary_path = Path(summary_out)
elif artifact_dir:
    summary_path = Path(artifact_dir) / "monitoring-summary.local.json"

if evidence_out:
    evidence_path = Path(evidence_out)
elif artifact_dir:
    evidence_path = Path(artifact_dir) / "monitoring-evidence.local.json"

if summary_path:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[monitoring-summary] summary written to {summary_path}")

if evidence_path:
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[monitoring-summary] evidence written to {evidence_path}")
