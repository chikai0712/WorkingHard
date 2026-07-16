"""routes/infra.py — 系統狀態、容器管理、排程、Findings、AI 劇本。"""
from __future__ import annotations
import json
import subprocess
import threading
import uuid
from datetime import datetime

import requests
from flask import Blueprint, jsonify, request

from core.config import DD_URL, DD_TOKEN
from core.job_store import jobs, log

bp = Blueprint("infra", __name__)

schedules: list[dict] = []


@bp.route("/api/findings")
def api_findings():
    severity = request.args.get("severity", "")
    limit    = int(request.args.get("limit", 50))
    offset   = int(request.args.get("offset", 0))
    try:
        params = {"limit": limit, "offset": offset}
        if severity:
            params["severity"] = severity
        r = requests.get(f"{DD_URL}/api/v2/findings/",
                         headers={"Authorization": f"Token {DD_TOKEN}"},
                         params=params, timeout=10)
        r.raise_for_status()
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e), "count": 0, "results": []}), 200


@bp.route("/api/status")
def api_status():
    status: dict = {}

    try:
        r = requests.get(f"{DD_URL}/api/v2/user_profile/",
                         headers={"Authorization": f"Token {DD_TOKEN}"}, timeout=5)
        status["defectdojo"] = {"ok": r.status_code == 200, "code": r.status_code}
    except Exception as e:
        status["defectdojo"] = {"ok": False, "error": str(e)}

    try:
        result = subprocess.run(["kubectl", "get", "scans", "-A", "--no-headers"],
                                capture_output=True, text=True, timeout=5)
        scan_count = len([l for l in result.stdout.strip().splitlines() if l.strip()])
        status["k8s"] = {"ok": result.returncode == 0, "scan_count": scan_count}
    except Exception as e:
        status["k8s"] = {"ok": False, "error": str(e)}

    try:
        r = requests.get("http://localhost:9001/minio/health/live", timeout=3)
        status["minio"] = {"ok": r.status_code == 200}
    except Exception as e:
        status["minio"] = {"ok": False, "error": str(e)}

    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=5)
        containers = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                containers.append({"name": parts[0], "status": parts[1]})
        status["docker"] = {"ok": True, "containers": containers}
    except Exception as e:
        status["docker"] = {"ok": False, "error": str(e)}

    return jsonify(status)


@bp.route("/api/schedules", methods=["GET"])
def api_schedules_get():
    return jsonify(schedules)


@bp.route("/api/schedules", methods=["POST"])
def api_schedules_post():
    data = request.get_json(force=True, silent=True) or {}
    schedule = {
        "id":         str(uuid.uuid4())[:8],
        "name":       data.get("name", "未命名"),
        "target":     data.get("target", ""),
        "templates":  data.get("templates", "exposure"),
        "cron":       data.get("cron", "0 2 * * *"),
        "enabled":    True,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "last_run":   None,
    }
    schedules.append(schedule)
    return jsonify(schedule), 201


@bp.route("/api/schedules/<sid>", methods=["DELETE"])
def api_schedules_delete(sid: str):
    schedules[:] = [s for s in schedules if s["id"] != sid]
    return jsonify({"ok": True})


@bp.route("/api/schedules/<sid>/toggle", methods=["POST"])
def api_schedules_toggle(sid: str):
    for s in schedules:
        if s["id"] == sid:
            s["enabled"] = not s["enabled"]
            return jsonify(s)
    return jsonify({"error": "not found"}), 404


@bp.route("/api/containers")
def api_containers():
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format",
             '{"id":"{{.ID}}","name":"{{.Names}}","image":"{{.Image}}",'
             '"status":"{{.Status}}","state":"{{.State}}","ports":"{{.Ports}}"}'],
            capture_output=True, text=True, timeout=8)
        containers = []
        for line in result.stdout.strip().splitlines():
            try:
                containers.append(json.loads(line))
            except Exception:
                pass
        return jsonify(containers)
    except Exception as e:
        return jsonify({"error": str(e)}), 200


@bp.route("/api/containers/<cid>/start", methods=["POST"])
def api_container_start(cid: str):
    try:
        r = subprocess.run(["docker", "start", cid], capture_output=True, text=True, timeout=10)
        return jsonify({"ok": r.returncode == 0, "out": r.stdout.strip() or r.stderr.strip()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@bp.route("/api/containers/<cid>/stop", methods=["POST"])
def api_container_stop(cid: str):
    try:
        r = subprocess.run(["docker", "stop", cid], capture_output=True, text=True, timeout=15)
        return jsonify({"ok": r.returncode == 0, "out": r.stdout.strip() or r.stderr.strip()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@bp.route("/api/containers/<cid>/restart", methods=["POST"])
def api_container_restart(cid: str):
    try:
        r = subprocess.run(["docker", "restart", cid], capture_output=True, text=True, timeout=20)
        return jsonify({"ok": r.returncode == 0, "out": r.stdout.strip() or r.stderr.strip()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@bp.route("/api/ai/playbook", methods=["POST"])
def api_ai_playbook():
    data    = request.get_json(force=True, silent=True) or {}
    target  = data.get("target", "")
    findings= data.get("findings", [])
    job_id  = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "logs": [], "current_step": "ai"}

    def _run():
        log(job_id, f"AI 攻擊劇本分析中（目標：{target}）...")
        try:
            prompt = (f"你是紅隊滲透測試專家。目標：{target}\n"
                      f"Findings：{json.dumps(findings[:10], ensure_ascii=False)}\n"
                      "請提供 3 個具體攻擊建議，包含工具指令。")
            r = requests.post("http://localhost:11434/api/generate",
                              json={"model": "llama3.2:3b", "prompt": prompt, "stream": False},
                              timeout=120)
            if r.status_code == 200:
                text = r.json().get("response", "")
                for line in text.splitlines():
                    log(job_id, line)
                jobs[job_id]["status"] = "done"
            else:
                log(job_id, f"[錯誤] Ollama 回應 {r.status_code}")
                jobs[job_id]["status"] = "failed"
        except Exception as e:
            log(job_id, f"[錯誤] {e}")
            jobs[job_id]["status"] = "failed"

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"job_id": job_id})
