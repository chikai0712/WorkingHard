"""ZAP DAST engine — daemon API 模式 + 臨時 container fallback。"""
from __future__ import annotations
import subprocess
import time
from pathlib import Path

import requests

from core.job_store import log
from core.config import ZAP_API, ZAP_KEY


def run_zap(job_id: str, target: str) -> dict:
    """執行 ZAP 掃描，回傳 {"ok": bool, "skipped": bool, "output_path": str|None}"""
    zap_out = f"/tmp/zap-{job_id}.xml"
    zap_target = target if target.startswith(("http://", "https://")) else f"https://{target}"
    log(job_id, f"  ZAP 掃描開始（目標：{zap_target}）...")

    # 快速探測 daemon
    zap_daemon_ok = False
    try:
        ping = requests.get(f"{ZAP_API}/JSON/core/view/version/",
                            params={"apikey": ZAP_KEY}, timeout=5)
        if ping.status_code == 200:
            zap_daemon_ok = True
            log(job_id, f"  ZAP daemon ready（{ping.json().get('version','')}），使用 daemon API 模式")
    except Exception:
        pass

    if not zap_daemon_ok:
        log(job_id, "  ZAP daemon 不可用，切換為臨時 container 模式...")

    try:
        if zap_daemon_ok:
            return _daemon_scan(job_id, zap_target, zap_out)
        else:
            return _container_scan(job_id, zap_target, zap_out)
    except requests.exceptions.ConnectionError:
        log(job_id, "  [警告] ZAP daemon 連線失敗，跳過 ZAP 掃描")
        return {"ok": True, "skipped": True}
    except subprocess.TimeoutExpired:
        log(job_id, "  [警告] ZAP 掃描逾時，跳過")
        return {"ok": True, "skipped": True}
    except Exception as e:
        log(job_id, f"  [警告] ZAP 例外: {e}，跳過")
        return {"ok": True, "skipped": True}


def _daemon_scan(job_id: str, zap_target: str, zap_out: str) -> dict:
    """模式 A：ZAP daemon API — Spider + Active Scan"""
    # Spider
    sp = requests.get(f"{ZAP_API}/JSON/spider/action/scan/",
                      params={"apikey": ZAP_KEY, "url": zap_target,
                              "recurse": "true", "maxChildren": "50"},
                      timeout=30)
    sp.raise_for_status()
    spider_id = sp.json().get("scan", "0")
    log(job_id, f"  [Spider] 開始 (id={spider_id}, maxChildren=50)...")
    for _ in range(24):
        time.sleep(5)
        prog = requests.get(f"{ZAP_API}/JSON/spider/view/status/",
                            params={"apikey": ZAP_KEY, "scanId": spider_id}, timeout=30)
        pct = prog.json().get("status", "0")
        log(job_id, f"  [Spider] {pct}%")
        if pct == "100":
            break
    url_count = len(requests.get(
        f"{ZAP_API}/JSON/spider/view/results/",
        params={"apikey": ZAP_KEY, "scanId": spider_id}, timeout=10
    ).json().get("results", []))
    log(job_id, f"  [Spider] 完成，發現 {url_count} 個 URL")

    # 停用耗時 scanner
    for sid in ["90019", "90020", "40034", "40035"]:
        requests.get(f"{ZAP_API}/JSON/ascan/action/disableScanners/",
                     params={"apikey": ZAP_KEY, "ids": sid}, timeout=10)

    # Active Scan
    asc = requests.get(f"{ZAP_API}/JSON/ascan/action/scan/",
                       params={"apikey": ZAP_KEY, "url": zap_target, "recurse": "false"},
                       timeout=30)
    asc.raise_for_status()
    scan_id = asc.json().get("scan", "0")
    log(job_id, f"  [Active Scan] 開始 (id={scan_id}, recurse=false)...")
    last_pct = "-1"
    for _ in range(60):
        time.sleep(10)
        try:
            prog = requests.get(f"{ZAP_API}/JSON/ascan/view/status/",
                                params={"apikey": ZAP_KEY, "scanId": scan_id}, timeout=30)
            pct = prog.json().get("status", "0")
        except requests.exceptions.ConnectionError:
            log(job_id, "  [Active Scan] ZAP daemon 斷線，取目前結果...")
            break
        if pct != last_pct:
            log(job_id, f"  [Active Scan] {pct}%")
            last_pct = pct
        if pct == "100":
            break

    try:
        alert_count = int(requests.get(
            f"{ZAP_API}/JSON/core/view/numberOfAlerts/",
            params={"apikey": ZAP_KEY, "baseurl": zap_target}, timeout=30
        ).json().get("numberOfAlerts", 0))
        log(job_id, f"  [Active Scan] 完成，發現 {alert_count} 個 alerts")
        alerts_resp = requests.get(
            f"{ZAP_API}/OTHER/core/other/xmlreport/",
            params={"apikey": ZAP_KEY}, timeout=60
        )
        alerts_resp.raise_for_status()
        with open(zap_out, "wb") as fh:
            fh.write(alerts_resp.content)
        log(job_id, f"  ✓ ZAP 完成（daemon 模式）：{alert_count} alerts")
        return {"ok": True, "output_path": zap_out}
    except requests.exceptions.ConnectionError:
        log(job_id, "  [警告] ZAP daemon 已斷線，無法取得報告，跳過")
        return {"ok": True, "skipped": True}


def _container_scan(job_id: str, zap_target: str, zap_out: str) -> dict:
    """模式 B：臨時 container fallback — zap-baseline.py"""
    is_external = not any(x in zap_target for x in
                          ["localhost", "127.0.0.1", "crapi", "dvwa", "192.168."])
    net = "bridge" if is_external else "docker_lab-network"
    log(job_id, f"  ZAP daemon 不可用，用臨時 container（network={net}）...")
    zap_cmd = [
        "docker", "run", "--rm",
        "--network", net,
        "-v", "/tmp:/zap/wrk",
        "zaproxy/zap-stable:2.17.0",
        "zap-baseline.py",
        "-t", zap_target,
        "-x", f"zap-{job_id}.xml",
        "-I",
    ]
    proc = subprocess.Popen(
        zap_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    for line in proc.stdout:
        line = line.rstrip()
        if line and not line.startswith("WARN"):
            log(job_id, f"  {line[:150]}")
    proc.wait()
    if Path(zap_out).exists() and Path(zap_out).stat().st_size > 0:
        alert_count = Path(zap_out).read_bytes().count(b"<alertitem>")
        log(job_id, f"  ✓ ZAP 完成（container 模式）：{alert_count} alerts")
        return {"ok": True, "output_path": zap_out}
    else:
        log(job_id, "  [警告] ZAP 臨時 container 無輸出，跳過")
        return {"ok": True, "skipped": True}
