#!/usr/bin/env python3
"""
RedSaaS CLI — 一鍵掃描到報告

使用方式：
    cd /Users/ckchiu/Desktop/Project/05-Services/RedSaaS
    source report-generator/.venv/bin/activate

    # 基本用法
    python scan.py --target http://your-target.com --name "客戶名稱"

    # 指定 template 和輸出路徑
    python scan.py --target http://crapi-web \
                   --name "crAPI 測試" \
                   --templates gambling \
                   --output reports/crapi-report.docx

    # 只掃不出報告
    python scan.py --target http://crapi-web --name "快速掃描" --no-report

需求：
    - Docker 已啟動（docker compose --profile reporting up -d）
    - report-generator/.venv 已安裝依賴
    - Ollama 已安裝並有 llama3.2:3b 模型
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

DD_URL = "http://localhost:8001"
DD_TOKEN = "8d6ba6cb54daa324785e12667d2af63c7d471e16"
DOCKER_DIR = Path(__file__).parent / "lab" / "docker"
REPORT_SCRIPT = Path(__file__).parent / "report-generator" / "generate_report.py"
VENV_PYTHON = Path(__file__).parent / "report-generator" / ".venv" / "bin" / "python3"


def log(step: int, total: int, msg: str):
    print(f"[{step}/{total}] {msg}")


def check_services():
    """確認 DefectDojo 和 Docker 服務正常。"""
    try:
        resp = requests.get(f"{DD_URL}/api/v2/users/", headers={"Authorization": f"Token {DD_TOKEN}"}, timeout=5)
        if resp.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        pass
    return False


def start_services():
    """啟動 reporting profile 的 Docker 服務。"""
    print("      正在啟動 DefectDojo 服務...")
    result = subprocess.run(
        ["docker", "compose", "--profile", "reporting", "up", "-d"],
        cwd=DOCKER_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"      [錯誤] {result.stderr}")
        return False

    print("      等待 DefectDojo 就緒（最多 60 秒）...")
    for _ in range(12):
        time.sleep(5)
        if check_services():
            return True
    return False


def run_nuclei(target: str, templates: str, output_file: Path) -> bool:
    """在 Docker 容器內執行 nuclei 掃描。"""
    if templates == "gambling":
        template_args = ["-t", "/templates/gambling/"]
    elif templates == "exposure":
        template_args = ["-t", "/root/nuclei-templates/http/misconfiguration/",
                         "-t", "/root/nuclei-templates/http/exposures/"]
    else:
        template_args = ["-tags", templates]

    cmd = [
        "docker", "compose", "--profile", "scan", "run", "--rm", "nuclei",
        "-u", target,
        *template_args,
        "-o", f"/output/{output_file.name}",
        "-jsonl",
    ]

    print(f"      目標：{target}")
    print(f"      Templates：{templates}")

    result = subprocess.run(cmd, cwd=DOCKER_DIR, capture_output=True, text=True)

    local_output = DOCKER_DIR / "scan-results" / output_file.name
    if local_output.exists() and local_output.stat().st_size > 0:
        return True

    if "No results found" in result.stderr or "No results found" in result.stdout:
        print("      掃描完成，無發現（No results found）")
        local_output.touch()
        return True

    if result.returncode != 0:
        print(f"      [錯誤] nuclei 執行失敗：{result.stderr[-300:]}")
        return False

    return True


def create_product_and_engagement(name: str) -> tuple[int, int]:
    """在 DefectDojo 建立 Product 和 Engagement，回傳 (product_id, engagement_id)。"""
    headers = {"Authorization": f"Token {DD_TOKEN}", "Content-Type": "application/json"}
    today = datetime.now().strftime("%Y-%m-%d")

    # 先找或建立 Product Type
    resp = requests.get(f"{DD_URL}/api/v2/product_types/?name=RedSaaS", headers=headers, timeout=10)
    data = resp.json()
    if data["count"] > 0:
        pt_id = data["results"][0]["id"]
    else:
        resp = requests.post(f"{DD_URL}/api/v2/product_types/",
                             headers=headers, json={"name": "RedSaaS"}, timeout=10)
        pt_id = resp.json()["id"]

    # 找或建立 Product
    resp = requests.get(f"{DD_URL}/api/v2/products/?name={name}", headers=headers, timeout=10)
    data = resp.json()
    if data["count"] > 0:
        product_id = data["results"][0]["id"]
    else:
        resp = requests.post(f"{DD_URL}/api/v2/products/",
                             headers=headers,
                             json={"name": name, "description": f"RedSaaS 掃描：{name}", "prod_type": pt_id},
                             timeout=10)
        resp.raise_for_status()
        product_id = resp.json()["id"]

    # 建立新 Engagement
    eng_name = f"{name} — {today}"
    resp = requests.post(f"{DD_URL}/api/v2/engagements/",
                         headers=headers,
                         json={
                             "name": eng_name,
                             "product": product_id,
                             "target_start": today,
                             "target_end": today,
                             "engagement_type": "CI/CD",
                             "status": "In Progress",
                         },
                         timeout=10)
    resp.raise_for_status()
    engagement_id = resp.json()["id"]

    return product_id, engagement_id


def import_scan(engagement_id: int, scan_file: Path) -> bool:
    """把 nuclei 結果匯入 DefectDojo。"""
    if scan_file.stat().st_size == 0:
        print("      掃描結果為空，跳過匯入")
        return True

    headers = {"Authorization": f"Token {DD_TOKEN}"}
    with open(scan_file, "rb") as f:
        resp = requests.post(
            f"{DD_URL}/api/v2/import-scan/",
            headers=headers,
            files={"file": (scan_file.name, f, "application/json")},
            data={
                "scan_type": "Nuclei Scan",
                "engagement": engagement_id,
                "minimum_severity": "Info",
            },
            timeout=60,
        )

    if resp.status_code in (200, 201):
        result = resp.json()
        print(f"      匯入成功，Test ID：{result.get('test')}")
        return True
    else:
        print(f"      [錯誤] 匯入失敗：{resp.text[:200]}")
        return False


def generate_report(engagement_id: int, output: Path) -> bool:
    """呼叫 report-generator 生成 Word 報告。"""
    python = VENV_PYTHON if VENV_PYTHON.exists() else sys.executable
    cmd = [
        str(python), str(REPORT_SCRIPT),
        "--dd-url", DD_URL,
        "--dd-token", DD_TOKEN,
        "--engagement-id", str(engagement_id),
        "--output", str(output),
        "--model", "llama3.2:3b",
    ]
    result = subprocess.run(cmd, text=True)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="RedSaaS 一鍵掃描到報告",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--target", required=True, help="掃描目標 URL，例如 http://crapi-web")
    parser.add_argument("--name", required=True, help="專案名稱，用於 DefectDojo Product 和報告標題")
    parser.add_argument("--templates", default="exposure",
                        help="掃描 templates：gambling / exposure / 任意 nuclei tag（預設：exposure）")
    parser.add_argument("--output", default=None, help="報告輸出路徑（預設：reports/<name>-<date>.docx）")
    parser.add_argument("--no-report", action="store_true", help="跳過報告生成，只掃描並匯入")
    args = parser.parse_args()

    today = datetime.now().strftime("%Y%m%d")
    scan_filename = f"scan-{args.name.replace(' ', '_')}-{today}.jsonl"
    scan_file = DOCKER_DIR / "scan-results" / scan_filename

    if args.output:
        report_output = Path(args.output)
    else:
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        report_output = reports_dir / f"{args.name.replace(' ', '_')}-{today}.docx"

    total_steps = 4 if not args.no_report else 3
    print(f"\n{'='*50}")
    print(f"  RedSaaS 掃描任務")
    print(f"  目標：{args.target}")
    print(f"  專案：{args.name}")
    print(f"{'='*50}\n")

    # Step 1 — 確認服務
    log(1, total_steps, "確認 DefectDojo 服務狀態...")
    if not check_services():
        print("      DefectDojo 未就緒，嘗試啟動...")
        if not start_services():
            print("\n[失敗] 無法啟動 DefectDojo，請手動執行：")
            print(f"  cd {DOCKER_DIR} && docker compose --profile reporting up -d")
            sys.exit(1)
    print("      DefectDojo 就緒 ✓")

    # Step 2 — 執行掃描
    log(2, total_steps, "執行 Nuclei 掃描...")
    if not run_nuclei(args.target, args.templates, scan_file):
        print("\n[失敗] 掃描失敗，請檢查目標是否可達")
        sys.exit(1)
    print(f"      掃描完成，結果：{scan_file}")

    # Step 3 — 匯入 DefectDojo
    log(3, total_steps, f"建立 DefectDojo 記錄並匯入結果...")
    product_id, engagement_id = create_product_and_engagement(args.name)
    print(f"      Product ID：{product_id}，Engagement ID：{engagement_id}")
    if not import_scan(engagement_id, scan_file):
        print("      [警告] 匯入失敗，繼續生成報告（使用空資料）")

    if args.no_report:
        print(f"\n完成！DefectDojo：{DD_URL}/engagement/{engagement_id}/")
        sys.exit(0)

    # Step 4 — 生成報告
    log(4, total_steps, f"生成中文報告（Ollama llama3.2:3b）...")
    print(f"      輸出路徑：{report_output}")
    if not generate_report(engagement_id, report_output):
        print("\n[失敗] 報告生成失敗")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  完成！")
    print(f"  DefectDojo：{DD_URL}/engagement/{engagement_id}/")
    print(f"  報告：{report_output.absolute()}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
