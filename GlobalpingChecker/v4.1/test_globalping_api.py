#!/usr/bin/env python3
"""
直接測試 Globalping API
"""
import json

# 使用 curl 測試 API
import subprocess

token = "uh5vlg4ttg3v5gwby5zgtqrciimahql5"

print("=" * 60)
print("🔍 測試 Globalping API")
print("=" * 60)

# 1. 測試 limits 端點
print("\n1️⃣  測試 /limits 端點")
print("-" * 60)
cmd = [
    "curl", "-s", "-X", "GET",
    "https://api.globalping.io/v1/limits",
    "-H", f"Authorization: Bearer {token}",
    "-H", "Content-Type: application/json"
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
print(f"Status: {result.returncode}")
print(f"Output: {result.stdout[:500]}")
if result.stderr:
    print(f"Error: {result.stderr[:500]}")

# 2. 測試 measurements 端點（創建測試）
print("\n2️⃣  測試 /measurements 端點（創建測試）")
print("-" * 60)

test_payload = {
    "type": "http",
    "target": "example.com",
    "inProgressUpdates": False,
    "options": {
        "method": "HEAD"
    }
}

cmd = [
    "curl", "-s", "-X", "POST",
    "https://api.globalping.io/v1/measurements",
    "-H", f"Authorization: Bearer {token}",
    "-H", "Content-Type: application/json",
    "-d", json.dumps(test_payload)
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
print(f"Status: {result.returncode}")
print(f"Output: {result.stdout[:500]}")
if result.stderr:
    print(f"Error: {result.stderr[:500]}")

print("\n" + "=" * 60)
