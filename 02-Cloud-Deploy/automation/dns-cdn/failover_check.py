#!/usr/bin/env python3
import json
import os
from pathlib import Path

TARGET = os.getenv("TARGET_DOMAIN", "example.com")
DRY_RUN = os.getenv("DRY_RUN", "true")
script_dir = Path(__file__).resolve().parent

result = {
    "target": TARGET,
    "dns_status": "unknown",
    "cdn_guess": "unknown",
    "action": "no-op" if DRY_RUN == "true" else "manual-review-required",
    "templates": {
        "failover_policy": str(script_dir / "failover-policy.example.yaml"),
        "cloudflare_record": str(script_dir / "providers" / "cloudflare-record.example.yaml"),
        "route53_record": str(script_dir / "providers" / "route53-record.example.yaml"),
    },
}

print(json.dumps(result, indent=2))
