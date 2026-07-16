"""report_engine — 呼叫 generate_report.py 在背景生成 Word 報告。"""
from __future__ import annotations
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from core.config import DD_URL, DD_TOKEN, REPORTS_DIR, REPORT_SCRIPT, VENV_PYTHON
from core.job_store import log


def run_report(job_id: str, target: str, jobs: dict) -> dict:
    eng_id = jobs[job_id].get("dd_engagement_id")
    if not eng_id:
        log(job_id, "  DefectDojo engagement 未建立，跳過報告")
        return {"ok": True, "skipped": True}

    today    = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = jobs[job_id].get("name", target).replace(" ", "_")
    out_path  = str(REPORTS_DIR / f"report-{safe_name}-{today}.docx")
    log(job_id, f"  AI 報告背景生成中（engagement {eng_id}），完成後儲存至 reports/...")

    def _gen():
        try:
            cmd = [
                str(VENV_PYTHON), str(REPORT_SCRIPT),
                "--dd-url", DD_URL,
                "--dd-token", DD_TOKEN,
                "--engagement-id", str(eng_id),
                "--output", out_path,
                "--model", "llama3.2:3b",
                "--target", target,
                "--tools", "Nmap v7.95, Nuclei v3.11, OWASP ZAP",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if proc.returncode == 0:
                jobs[job_id]["report_path"] = out_path
                log(job_id, f"  ✓ AI 報告已儲存：{Path(out_path).name}")
            else:
                log(job_id, f"  [警告] 報告生成失敗: {proc.stderr[:120]}")
        except subprocess.TimeoutExpired:
            log(job_id, "  [警告] 報告生成逾時（600s）")
        except Exception as e:
            log(job_id, f"  [警告] 報告生成例外: {e}")

    threading.Thread(target=_gen, daemon=True).start()
    return {"ok": True, "async": True}
