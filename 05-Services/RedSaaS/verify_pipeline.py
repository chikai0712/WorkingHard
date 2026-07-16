#!/usr/bin/env python3
"""
secureCodeBox 端對端 Pipeline 驗證腳本

驗證流程：
  1. 環境檢查（kubectl / k8s 連線 / MinIO port-forward）
  2. 觸發一次新的 nuclei scan
  3. 輪詢狀態直到 Done
  4. 從 MinIO 讀取 findings.json
  5. 印出摘要並判斷是否通過

使用方式：
  python verify_pipeline.py
  python verify_pipeline.py --target http://host.docker.internal:8888
  python verify_pipeline.py --timeout 300
"""

import argparse
import sys
import time
from datetime import datetime

# 直接重用現有的 scb_client
sys.path.insert(0, str(__file__[: __file__.rfind("/")]))
from scb_client import (
    submit_nuclei_scan,
    wait_for_scan,
    get_scan_status,
    get_findings,
    list_scans,
    ensure_minio_port_forward,
    TERMINAL_STATES,
)

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(msg: str):
    print(f"  {GREEN}✓{RESET} {msg}")


def fail(msg: str):
    print(f"  {RED}✗{RESET} {msg}")


def warn(msg: str):
    print(f"  {YELLOW}⚠{RESET} {msg}")


def info(msg: str):
    print(f"  {CYAN}→{RESET} {msg}")


def section(title: str):
    print(f"\n{BOLD}[{title}]{RESET}")


def check_kubectl() -> bool:
    import subprocess
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", "securecodebox-system", "--no-headers"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        fail(f"kubectl 無法連線：{result.stderr.strip()[:100]}")
        return False

    lines = [l for l in result.stdout.strip().split("\n") if l]
    running = [l for l in lines if "Running" in l]
    ok(f"k8s 連線正常，securecodebox-system 有 {len(running)}/{len(lines)} 個 pod Running")
    return True


def check_scanner_ready() -> bool:
    import subprocess
    result = subprocess.run(
        ["kubectl", "get", "scantypes", "-A", "--no-headers"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        fail(f"無法列出 ScanTypes：{result.stderr.strip()[:100]}")
        return False

    lines = [l for l in result.stdout.strip().split("\n") if "nuclei" in l.lower()]
    if not lines:
        fail("找不到 nuclei ScanType，請確認 nuclei scanner 已安裝")
        return False

    # 輸出格式：NAMESPACE   NAME   AGE
    first = lines[0].split()
    ns = first[0] if len(first) >= 2 else "unknown"
    name = first[1] if len(first) >= 2 else first[0]
    ok(f"nuclei ScanType 就緒：{name}（namespace: {ns}）")
    return True


def check_minio() -> bool:
    result = ensure_minio_port_forward()
    if result:
        ok("MinIO port-forward 可用（localhost:9001）")
    else:
        fail("MinIO port-forward 無法建立，findings 讀取將失敗")
    return result


def run_e2e_scan(target: str, timeout: int) -> dict:
    """執行端對端掃描並回傳結果"""
    info(f"提交 nuclei scan → {target}")
    scan_name = submit_nuclei_scan(target, templates="exposure")
    info(f"Scan 名稱：{scan_name}")

    states_seen = []

    def on_update(status: dict):
        state = status.get("state", "Unknown")
        if not states_seen or states_seen[-1] != state:
            states_seen.append(state)
            ts = datetime.now().strftime("%H:%M:%S")
            findings = status.get("findings_count", 0)
            info(f"[{ts}] 狀態：{state}  findings={findings}")

    info("等待掃描完成（每 5 秒輪詢一次）...")
    final_status = wait_for_scan(scan_name, timeout=timeout, poll_interval=5, on_update=on_update)
    final_status["states_seen"] = states_seen
    final_status["scan_name"] = scan_name
    return final_status


def validate_findings(scan_name: str) -> tuple[bool, list]:
    """從 MinIO 讀取並驗證 findings 格式"""
    info("從 MinIO 讀取 findings.json...")
    findings = get_findings(scan_name)

    if not findings:
        warn("findings 為空（目標可能沒有漏洞，或掃描無結果）")
        return True, []

    if isinstance(findings, list) and findings and "error" in findings[0]:
        fail(f"讀取 findings 失敗：{findings[0]['error']}")
        return False, []

    # 驗證 findings 格式
    required_fields = {"name", "severity", "identified_at", "location"}
    malformed = [f for f in findings if not required_fields.issubset(f.keys())]
    if malformed:
        warn(f"{len(malformed)} 筆 findings 格式不完整（缺少必要欄位）")

    ok(f"成功讀取 {len(findings)} 筆 findings")
    return True, findings


def print_findings_summary(findings: list):
    if not findings:
        return

    by_severity = {}
    for f in findings:
        sev = f.get("severity", "UNKNOWN")
        by_severity[sev] = by_severity.get(sev, 0) + 1

    print(f"\n  {'嚴重性':<12} {'數量':>6}")
    print(f"  {'-'*20}")
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "UNKNOWN"]
    for sev in severity_order:
        count = by_severity.get(sev, 0)
        if count > 0:
            color = RED if sev in ("CRITICAL", "HIGH") else YELLOW if sev == "MEDIUM" else RESET
            print(f"  {color}{sev:<12}{RESET} {count:>6}")

    print(f"\n  前 3 筆 findings：")
    for f in findings[:3]:
        name = f.get("name", "未知")[:55]
        sev = f.get("severity", "?")
        loc = f.get("location", "?")[:40]
        print(f"    [{sev}] {name}")
        print(f"         → {loc}")


def check_state_transitions(states_seen: list) -> bool:
    """驗證 scan 狀態有正常流轉"""
    expected_final = {"Done", "Errored", "Aborted"}
    if not states_seen:
        fail("沒有觀察到任何狀態變化")
        return False

    final = states_seen[-1]
    if final not in expected_final:
        fail(f"Scan 未到達終態，最後狀態：{final}")
        return False

    if final == "Done":
        ok(f"狀態流轉正常：{' → '.join(states_seen)}")
        return True
    elif final == "Errored":
        fail(f"Scan 以 Errored 結束，流轉：{' → '.join(states_seen)}")
        return False
    else:
        warn(f"Scan 以 {final} 結束，流轉：{' → '.join(states_seen)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="secureCodeBox 端對端 Pipeline 驗證")
    parser.add_argument("--target", default="http://host.docker.internal:8888",
                        help="掃描目標（預設：http://host.docker.internal:8888）")
    parser.add_argument("--timeout", type=int, default=300,
                        help="等待 scan 完成的最大秒數（預設：300）")
    parser.add_argument("--skip-minio", action="store_true",
                        help="跳過 MinIO findings 讀取（只驗證 scan 狀態）")
    args = parser.parse_args()

    print(f"\n{BOLD}{'='*55}{RESET}")
    print(f"{BOLD}  secureCodeBox Pipeline 驗證{RESET}")
    print(f"  目標：{args.target}")
    print(f"  時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{BOLD}{'='*55}{RESET}")

    results = {}

    # ── 層次 1：環境檢查 ──
    section("層次 1｜環境檢查")
    results["kubectl"] = check_kubectl()
    results["scanner"] = check_scanner_ready()
    if not args.skip_minio:
        results["minio"] = check_minio()

    if not results["kubectl"] or not results["scanner"]:
        fail("環境檢查未通過，中止驗證")
        sys.exit(1)

    # ── 層次 2：端對端掃描 ──
    section("層次 2｜觸發端對端掃描")
    try:
        final_status = run_e2e_scan(args.target, args.timeout)
    except Exception as e:
        fail(f"掃描過程發生例外：{e}")
        sys.exit(1)

    state = final_status.get("state", "Unknown")
    states_seen = final_status.get("states_seen", [])
    findings_count = final_status.get("findings_count", 0)
    scan_name = final_status.get("scan_name", "")

    results["scan_state"] = check_state_transitions(states_seen)
    info(f"最終 findings 數量（operator 統計）：{findings_count}")

    # ── 層次 3：Findings 讀取與格式驗證 ──
    if not args.skip_minio and state == "Done":
        section("層次 3｜Findings 讀取與格式驗證")
        findings_ok, findings = validate_findings(scan_name)
        results["findings"] = findings_ok
        if findings_ok:
            print_findings_summary(findings)
    elif args.skip_minio:
        warn("跳過 MinIO findings 讀取（--skip-minio）")

    # ── 最終結論 ──
    section("驗證結論")
    passed = all(v for v in results.values())
    total = len(results)
    passed_count = sum(1 for v in results.values() if v)

    for check_name, result in results.items():
        label = {
            "kubectl": "k8s 連線",
            "scanner": "nuclei ScanType",
            "minio": "MinIO 連線",
            "scan_state": "Scan 狀態流轉",
            "findings": "Findings 格式",
        }.get(check_name, check_name)
        if result:
            ok(label)
        else:
            fail(label)

    print()
    if passed:
        print(f"{BOLD}{GREEN}  ✓ 全部通過（{passed_count}/{total}）— Pipeline 運作正常{RESET}")
        print(f"  Scan 名稱：{scan_name}")
    else:
        print(f"{BOLD}{RED}  ✗ 未完全通過（{passed_count}/{total}）{RESET}")

    print(f"{BOLD}{'='*55}{RESET}\n")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
