"""api_engine — DefectDojo import-scan 匯入。"""
from __future__ import annotations
import csv
import io
from pathlib import Path

import requests

from core.config import DD_URL, DD_TOKEN
from core.job_store import log


def _gobuster_to_generic_csv(gobuster_file: str, target: str) -> str | None:
    """把 gobuster txt 輸出轉成 DefectDojo Generic Findings Import CSV。
    只保留 200/301/302/307/308（可訪問），過濾 403/404/410。
    """
    from datetime import datetime
    interesting = {"200", "301", "302", "307", "308"}
    today = datetime.now().strftime("%Y-%m-%d")
    rows = []
    for line in Path(gobuster_file).read_text(errors="replace").splitlines():
        line = line.strip()
        if not line or "(Status:" not in line:
            continue
        try:
            path_part = line.split("(Status:")[0].strip()
            status    = line.split("(Status:")[1].split(")")[0].strip()
        except IndexError:
            continue
        if status not in interesting:
            continue
        url   = target.rstrip("/") + path_part
        title = f"發現可訪問路徑：{path_part} [{status}]"
        desc  = f"Gobuster 路徑枚舉發現路徑 {url} 回應 HTTP {status}，請確認是否應對外開放。"
        rows.append({
            "Date": today, "Title": title, "CweId": 0,
            "Url": url, "Severity": "Info",
            "Description": desc,
            "Mitigation": "確認此路徑是否應對外開放，如不需要請限制存取。",
            "Impact": "攻擊者可能藉此列舉網站結構。",
            "References": url,
            "Active": "True", "Verified": "True",
        })

    if not rows:
        return None

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=[
        "Date","Title","CweId","Url","Severity",
        "Description","Mitigation","Impact","References","Active","Verified"
    ])
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def run_api_import(job_id: str, jobs: dict) -> dict:
    eng_id       = jobs[job_id].get("dd_engagement_id")
    nuclei_file  = jobs[job_id].get("last_scan_output")
    zap_file     = jobs[job_id].get("zap_output")
    gobuster_file= jobs[job_id].get("gobuster_output")
    nikto_file   = f"/tmp/nikto-{job_id}.xml"

    scan_files: list[tuple[str, str]] = []
    if nuclei_file and Path(nuclei_file).exists():
        scan_files.append((nuclei_file, "Nuclei Scan"))
    if zap_file and Path(zap_file).exists():
        scan_files.append((zap_file, "ZAP Scan"))
    if Path(nikto_file).exists() and Path(nikto_file).stat().st_size > 0:
        scan_files.append((nikto_file, "Nikto Scan"))

    if not scan_files and not gobuster_file:
        log(job_id, "  DefectDojo 離線或無 findings，跳過匯入")
        return {"ok": True, "skipped": True}

    if not eng_id:
        log(job_id, "  DefectDojo engagement 未建立，跳過匯入")
        return {"ok": True, "skipped": True}

    all_ok  = True
    headers = {"Authorization": f"Token {DD_TOKEN}"}

    for scan_file, scan_type in scan_files:
        try:
            log(job_id, f"  匯入 {Path(scan_file).name} ({scan_type}) → engagement {eng_id}...")
            with open(scan_file, "rb") as fh:
                resp = requests.post(
                    f"{DD_URL}/api/v2/import-scan/",
                    headers=headers,
                    data={"engagement": eng_id, "scan_type": scan_type,
                          "verified": "true", "active": "true",
                          "close_old_findings": "true",
                          "deduplication_on_engagement": "true"},
                    files={"file": fh},
                    timeout=30,
                )
            if resp.status_code in (200, 201):
                log(job_id, f"  ✓ {scan_type} 匯入成功")
            else:
                log(job_id, f"  [警告] {scan_type} 匯入失敗: {resp.status_code} {resp.text[:80]}")
                all_ok = False
        except Exception as e:
            log(job_id, f"  [警告] {scan_type} 匯入例外: {e}")
            all_ok = False

    # Gobuster → Generic Findings Import CSV
    if gobuster_file and Path(gobuster_file).exists():
        target = jobs[job_id].get("name", "")
        csv_content = _gobuster_to_generic_csv(gobuster_file, target)
        if csv_content:
            try:
                log(job_id, f"  匯入 gobuster 結果（Generic Findings）→ engagement {eng_id}...")
                resp = requests.post(
                    f"{DD_URL}/api/v2/import-scan/",
                    headers=headers,
                    data={"engagement": eng_id,
                          "scan_type": "Generic Findings Import",
                          "verified": "true", "active": "true",
                          "close_old_findings": "false",
                          "deduplication_on_engagement": "true"},
                    files={"file": ("gobuster.csv",
                                    csv_content.encode("utf-8"),
                                    "text/csv")},
                    timeout=30,
                )
                if resp.status_code in (200, 201):
                    log(job_id, "  ✓ Gobuster 路徑匯入成功")
                else:
                    log(job_id, f"  [警告] Gobuster 匯入失敗: {resp.status_code} {resp.text[:80]}")
            except Exception as e:
                log(job_id, f"  [警告] Gobuster 匯入例外: {e}")
        else:
            log(job_id, "  Gobuster 無可訪問路徑（全為 403/404），跳過匯入")

    if all_ok:
        for scan_file, _ in scan_files:
            Path(scan_file).unlink(missing_ok=True)
        if gobuster_file:
            Path(gobuster_file).unlink(missing_ok=True)

    return {"ok": all_ok}
