#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from datetime import datetime, UTC
from pathlib import Path

family = os.getenv("DEVICE_FAMILY", "f5")
summary_out = os.getenv("SUMMARY_OUT", "")
evidence_out = os.getenv("EVIDENCE_OUT", "")
artifact_dir = os.getenv("ARTIFACT_DIR", "")

print(f"[ansible-summary] device_family={family}")
print("[ansible-summary] Step 1: inspect check-only output placeholders")
print("[ansible-summary] Step 2: normalize device consistency summary")
print("[ansible-summary] Step 3: no real device/API access in skeleton mode")

updated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
summary_payload = {
    "event_id": "ansible-summary-local",
    "module": "ansible",
    "device_family": family,
    "status": "warning",
    "summary": "Ansible consistency summary generated in skeleton mode; inventory and device evidence still require operator review.",
    "affected_devices": [f"{family}-sample-01"],
    "recommended_checks": [
        "Review inventory mapping",
        "Compare expected policy to check output",
        "Confirm approval boundary for network changes",
    ],
    "recommended_policy": "hold",
    "updated_at": updated_at,
}

evidence_payload = {
    "event_id": "ansible-evidence-local",
    "module": "ansible",
    "evidence_type": "consistency-check",
    "device_family": family,
    "status": "warning",
    "summary": "Ansible evidence generated in skeleton mode; device consistency observations still require operator review.",
    "affected_devices": [f"{family}-sample-01"],
    "observations": [
        {
            "name": "inventory_mapping_loaded",
            "status": "ok",
            "value": True,
            "notes": "Inventory mapping loaded in skeleton mode",
        },
        {
            "name": "policy_alignment",
            "status": "warning",
            "value": False,
            "notes": "Placeholder check output differs from expected policy",
        },
    ],
    "recommended_checks": [
        "Review inventory mapping",
        "Compare expected policy to check output",
        "Confirm approval boundary for network changes",
    ],
    "recommended_policy": "hold",
    "updated_at": updated_at,
}

summary_path: Path | None = None
evidence_path: Path | None = None
if summary_out:
    summary_path = Path(summary_out)
elif artifact_dir:
    summary_path = Path(artifact_dir) / f"ansible-summary.{family}.local.json"

if evidence_out:
    evidence_path = Path(evidence_out)
elif artifact_dir:
    evidence_path = Path(artifact_dir) / f"ansible-evidence.{family}.local.json"

if summary_path:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ansible-summary] summary written to {summary_path}")

if evidence_path:
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ansible-summary] evidence written to {evidence_path}")
