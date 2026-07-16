"""routes/scan.py — 掃描執行、狀態查詢、停止。"""
from __future__ import annotations
import uuid
from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, jsonify, request

from core.job_store import jobs, log
from core.executor import run_preset_job

bp = Blueprint("scan", __name__)
_executor = ThreadPoolExecutor(max_workers=4)


@bp.route("/api/preset/<preset_id>/run", methods=["POST"])
def api_run_preset(preset_id: str):
    data        = request.get_json(force=True, silent=True) or {}
    target      = data.get("target", "")
    name        = data.get("name", target)
    with_report = data.get("with_report", True)
    if not target:
        return jsonify({"error": "target required"}), 400

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "pending",
        "logs": [],
        "current_step": None,
        "name": name,
    }
    _executor.submit(run_preset_job, job_id, preset_id, target, name, with_report)
    return jsonify({"job_id": job_id})


@bp.route("/api/jobs")
def api_jobs():
    return jsonify({
        jid: {
            "status": j.get("status"),
            "current_step": j.get("current_step"),
            "log_count": len(j.get("logs", [])),
        }
        for jid, j in jobs.items()
    })


@bp.route("/api/status/<job_id>")
def api_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "status":       job.get("status"),
        "logs":         job.get("logs", []),
        "current_step": job.get("current_step"),
        "report_name":  job.get("report_name"),
        "report_path":  job.get("report_path"),
    })


@bp.route("/api/stop/<job_id>", methods=["POST"])
def api_stop(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404
    job["status"] = "stopped"
    log(job_id, "[使用者] 已手動停止")
    return jsonify({"ok": True})
