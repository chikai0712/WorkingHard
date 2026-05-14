#!/usr/bin/env python3
import json
import os
from pathlib import Path

provider = os.getenv("CLOUD_PROVIDER", "aws")
scope = os.getenv("REPORT_SCOPE", "monthly")
tag_key = os.getenv("TAG_KEY", "Owner")
dry_run = os.getenv("DRY_RUN", "true")
script_dir = Path(__file__).resolve().parent

report = {
    "provider": provider,
    "scope": scope,
    "tag_key": tag_key,
    "dry_run": dry_run,
    "checks": [
        "idle_compute_candidates",
        "orphaned_storage_candidates",
        "missing_tag_candidates",
        "budget_threshold_review",
    ],
    "templates": {
        "budget_thresholds": str(script_dir / "budget-thresholds.example.yaml"),
        "tag_audit_policy": str(script_dir / "tag-audit-policy.example.yaml"),
        "cost_dimensions": str(script_dir / "cost-dimensions.example.json"),
    },
}

print(json.dumps(report, indent=2))
