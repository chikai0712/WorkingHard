"""routes/reports.py — 報告檔案管理 + DefectDojo engagement 報告。"""
from __future__ import annotations
import subprocess
import threading
import uuid
from datetime import datetime
from pathlib import Path

import requests
from flask import Blueprint, jsonify, request, send_file

from core.config import DD_URL, DD_TOKEN, REPORTS_DIR, REPORT_SCRIPT, VENV_PYTHON
from core.job_store import jobs, log

bp = Blueprint("reports", __name__)

_SEV_ORDER = ["Critical", "High", "Medium", "Low", "Informational"]
_SEV_COLOR = {"Critical": "#fda4af", "High": "#fca5a5", "Medium": "#fde68a",
              "Low": "#93c5fd", "Informational": "#94a3b8"}


@bp.route("/api/reports/list")
def api_reports_list():
    archive_dir = REPORTS_DIR / "archive"
    archive_dir.mkdir(exist_ok=True)
    result = []
    for f in sorted(REPORTS_DIR.glob("*.docx"), key=lambda f: f.stat().st_mtime, reverse=True):
        result.append({"name": f.name, "size": f.stat().st_size, "archived": False,
                        "mtime": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "url": f"/api/reports/download/{f.name}"})
    for f in sorted(archive_dir.glob("*.docx"), key=lambda f: f.stat().st_mtime, reverse=True):
        result.append({"name": f.name, "size": f.stat().st_size, "archived": True,
                        "mtime": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "url": f"/api/reports/download-archive/{f.name}"})
    return jsonify(result)


@bp.route("/api/reports/download/<filename>")
def api_reports_download(filename: str):
    path = REPORTS_DIR / filename
    if not path.exists() or not path.name.endswith(".docx"):
        return jsonify({"error": "not found"}), 404
    return send_file(path, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@bp.route("/api/reports/download-archive/<filename>")
def api_reports_download_archive(filename: str):
    path = REPORTS_DIR / "archive" / filename
    if not path.exists() or not path.name.endswith(".docx"):
        return jsonify({"error": "not found"}), 404
    return send_file(path, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@bp.route("/api/reports/archive/<filename>", methods=["POST"])
def api_reports_archive(filename: str):
    src = REPORTS_DIR / filename
    if not src.exists() or not src.name.endswith(".docx"):
        return jsonify({"error": "not found"}), 404
    archive_dir = REPORTS_DIR / "archive"
    archive_dir.mkdir(exist_ok=True)
    src.rename(archive_dir / filename)
    return jsonify({"ok": True})


@bp.route("/api/reports/unarchive/<filename>", methods=["POST"])
def api_reports_unarchive(filename: str):
    src = REPORTS_DIR / "archive" / filename
    if not src.exists() or not src.name.endswith(".docx"):
        return jsonify({"error": "not found"}), 404
    (REPORTS_DIR / filename).write_bytes(src.read_bytes())
    src.unlink()
    return jsonify({"ok": True})


@bp.route("/api/reports/delete/<filename>", methods=["DELETE"])
def api_reports_delete(filename: str):
    for candidate in [REPORTS_DIR / filename, REPORTS_DIR / "archive" / filename]:
        if candidate.exists() and candidate.name.endswith(".docx"):
            candidate.unlink()
            return jsonify({"ok": True})
    return jsonify({"error": "not found"}), 404


@bp.route("/api/reports/generate", methods=["POST"])
def api_reports_generate():
    data         = request.get_json(force=True, silent=True) or {}
    eng_id       = data.get("engagement_id")
    name         = data.get("name", f"report-eng{eng_id}").replace(" ", "_")
    report_target= data.get("target", "")
    report_tools = data.get("tools", "Nmap v7.95, Nuclei v3.11, OWASP ZAP")
    if not eng_id:
        return jsonify({"error": "engagement_id required"}), 400

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "pending", "logs": [], "current_step": None}

    def _do_generate():
        try:
            today    = datetime.now().strftime("%Y%m%d-%H%M%S")
            out_path = str(REPORTS_DIR / f"report-{name}-{today}.docx")
            log(job_id, f"AI 報告生成開始（engagement {eng_id}）...")
            cmd = [str(VENV_PYTHON), str(REPORT_SCRIPT),
                   "--dd-url", DD_URL, "--dd-token", DD_TOKEN,
                   "--engagement-id", str(eng_id),
                   "--output", out_path, "--model", "llama3.2:3b",
                   "--target", report_target, "--tools", report_tools]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            for line in (proc.stdout or "").splitlines():
                if line.strip():
                    log(job_id, f"  {line}")
            if proc.returncode == 0:
                jobs[job_id]["report_path"] = out_path
                jobs[job_id]["status"]       = "done"
                log(job_id, f"✓ 報告已儲存：{Path(out_path).name}")
            else:
                jobs[job_id]["status"] = "failed"
                log(job_id, f"[錯誤] 生成失敗: {proc.stderr[:200]}")
        except subprocess.TimeoutExpired:
            jobs[job_id]["status"] = "failed"
            log(job_id, "[錯誤] 報告生成逾時（600s）")
        except Exception as e:
            jobs[job_id]["status"] = "failed"
            log(job_id, f"[錯誤] {e}")

    threading.Thread(target=_do_generate, daemon=True).start()
    return jsonify({"job_id": job_id, "engagement_id": eng_id})


@bp.route("/api/reports")
def api_reports():
    try:
        h = {"Authorization": f"Token {DD_TOKEN}"}
        eng_r = requests.get(f"{DD_URL}/api/v2/engagements/?limit=20&ordering=-id",
                              headers=h, timeout=8)
        eng_r.raise_for_status()
        result = []
        for e in eng_r.json().get("results", []):
            find_r   = requests.get(f"{DD_URL}/api/v2/findings/?test__engagement={e['id']}&limit=200",
                                    headers=h, timeout=8)
            findings = find_r.json().get("results", []) if find_r.ok else []
            sev = {s: 0 for s in _SEV_ORDER}
            for f in findings:
                sev[f.get("severity", "Informational")] = sev.get(f.get("severity", "Informational"), 0) + 1
            result.append({"id": e["id"], "name": e["name"], "product": e["product"],
                            "status": e["status"], "target_start": e.get("target_start", ""),
                            "findings_count": len(findings), "severity": sev})
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 200


@bp.route("/api/reports/<int:eid>/html")
def api_report_html(eid: int):
    try:
        h = {"Authorization": f"Token {DD_TOKEN}"}
        eng  = requests.get(f"{DD_URL}/api/v2/engagements/{eid}/", headers=h, timeout=8).json()
        find_r = requests.get(f"{DD_URL}/api/v2/findings/?test__engagement={eid}&limit=500",
                               headers=h, timeout=10)
        findings = find_r.json().get("results", []) if find_r.ok else []

        rows = ""
        for f in sorted(findings, key=lambda x: _SEV_ORDER.index(x.get("severity", "Informational"))
                         if x.get("severity") in _SEV_ORDER else 99):
            color = _SEV_COLOR.get(f.get("severity", "Informational"), "#94a3b8")
            rows += (f'<tr><td style="color:{color};font-weight:600">{f.get("severity","")}</td>'
                     f'<td>{f.get("title","")}</td>'
                     f'<td style="color:#64748b;font-size:.85em">{f.get("cve_references","") or "-"}</td>'
                     f'<td>{"Active" if f.get("active") else "Closed"}</td></tr>')

        sev_counts = {}
        for f in findings:
            s = f.get("severity", "Informational")
            sev_counts[s] = sev_counts.get(s, 0) + 1

        summary = "".join(
            f'<div style="text-align:center;padding:.75rem 1.5rem;background:#1e293b;'
            f'border-radius:8px;border:1px solid #334155">'
            f'<div style="font-size:1.8rem;font-weight:700;color:{_SEV_COLOR[s]}">{sev_counts.get(s,0)}</div>'
            f'<div style="font-size:.75rem;color:#64748b;margin-top:.2rem">{s}</div></div>'
            for s in _SEV_ORDER
        )
        html = (f'<!DOCTYPE html><html><head><meta charset="UTF-8">'
                f'<title>Scan Report — {eng["name"]}</title>'
                f'<style>body{{font-family:-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;'
                f'padding:2rem;max-width:1000px;margin:0 auto}}'
                f'h1{{color:#f1f5f9;font-size:1.5rem;margin-bottom:.25rem}}'
                f'.meta{{color:#64748b;font-size:.85rem;margin-bottom:2rem}}'
                f'.summary{{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:2rem}}'
                f'table{{width:100%;border-collapse:collapse;font-size:.85rem}}'
                f'th{{text-align:left;padding:.5rem .75rem;color:#64748b;border-bottom:1px solid #334155}}'
                f'td{{padding:.5rem .75rem;border-bottom:1px solid #1e293b}}'
                f'tr:hover td{{background:#1e293b}}</style></head><body>'
                f'<h1>滲透測試掃描報告</h1>'
                f'<div class="meta">Engagement：{eng["name"]} ｜ 狀態：{eng["status"]} ｜ '
                f'生成時間：{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>'
                f'<div class="summary">{summary}</div>'
                f'<table><thead><tr><th>嚴重度</th><th>漏洞名稱</th><th>CVE</th><th>狀態</th></tr></thead>'
                f'<tbody>{rows}</tbody></table>'
                f'<div style="margin-top:2rem;color:#475569;font-size:.78rem;text-align:center">'
                f'RedSaaS 自動化報告 — 共 {len(findings)} 筆 findings</div>'
                f'</body></html>')
        return html, 200, {"Content-Type": "text/html; charset=utf-8"}
    except Exception as e:
        return f"<pre>報告生成失敗：{e}</pre>", 500
