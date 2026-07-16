"""routes/lab.py — 服務群組一鍵開關。"""
from __future__ import annotations
import subprocess
import threading
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request

from core.config import DOCKER_DIR
from core.job_store import jobs, log

bp = Blueprint("lab", __name__)

# 服務群組定義：每個群組對應一組 docker-compose services
LAB_GROUPS = [
    {
        "id":    "core",
        "name":  "核心平台",
        "desc":  "DefectDojo 漏洞管理平台（必要）",
        "icon":  "🛡",
        "color": "#3b82f6",
        "services": [
            "defectdojo", "defectdojo-nginx",
            "defectdojo-worker", "defectdojo-db", "defectdojo-redis",
        ],
    },
    {
        "id":    "targets",
        "name":  "靶場環境",
        "desc":  "crAPI + DVWA 練習靶機",
        "icon":  "🎯",
        "color": "#f97316",
        "services": [
            "crapi-identity", "crapi-community", "crapi-workshop",
            "crapi-web", "crapi-postgres", "crapi-mongodb",
            "crapi-mailhog", "crapi-chatbot", "dvwa",
        ],
    },
    {
        "id":    "redteam",
        "name":  "紅隊工具",
        "desc":  "ZAP DAST 主動掃描代理",
        "icon":  "⚔️",
        "color": "#ef4444",
        "services": ["zap"],
    },
    {
        "id":    "platform",
        "name":  "分析平台",
        "desc":  "Elasticsearch + Kibana 日誌分析",
        "icon":  "📊",
        "color": "#8b5cf6",
        "services": ["elasticsearch", "kibana"],
    },
    {
        "id":    "reporting",
        "name":  "報告協作",
        "desc":  "Faraday 協作工作台",
        "icon":  "📝",
        "color": "#10b981",
        "services": ["faraday", "faraday-db"],
    },
    {
        "id":    "adrecon",
        "name":  "AD 偵察",
        "desc":  "BloodHound + Neo4j AD 攻擊路徑分析",
        "icon":  "🕸",
        "color": "#6366f1",
        "services": ["bloodhound", "bloodhound-db", "bloodhound-neo4j"],
    },
]


def _svc_state(service: str) -> str:
    """回傳 running / stopped / missing。"""
    try:
        r = subprocess.run(
            ["docker", "compose", "ps", "--format", "{{.Service}}\t{{.State}}", service],
            cwd=DOCKER_DIR, capture_output=True, text=True, timeout=6,
        )
        for line in r.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) == 2 and parts[0] == service:
                state = parts[1].lower()
                return "running" if "running" in state else "stopped"
        return "stopped"
    except Exception:
        return "missing"


def _group_status(group: dict) -> dict:
    """計算群組整體狀態：all_running / partial / stopped。"""
    states = [_svc_state(s) for s in group["services"]]
    running = sum(1 for s in states if s == "running")
    total   = len(states)
    if running == total:
        overall = "running"
    elif running == 0:
        overall = "stopped"
    else:
        overall = "partial"
    return {
        "id":       group["id"],
        "name":     group["name"],
        "desc":     group["desc"],
        "color":    group["color"],
        "overall":  overall,
        "running":  running,
        "total":    total,
        "details":  [{"service": s, "state": st}
                     for s, st in zip(group["services"], states)],
    }


@bp.route("/api/lab/groups")
def api_lab_groups():
    """回傳所有群組的即時狀態。"""
    return jsonify([_group_status(g) for g in LAB_GROUPS])


@bp.route("/api/lab/<group_id>/start", methods=["POST"])
def api_lab_start(group_id: str):
    group = next((g for g in LAB_GROUPS if g["id"] == group_id), None)
    if not group:
        return jsonify({"error": "group not found"}), 404

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "logs": [], "current_step": f"start:{group_id}"}

    def _start():
        log(job_id, f"▶ 啟動群組「{group['name']}」...")
        try:
            cmd = ["docker", "compose", "up", "-d", "--no-recreate"] + group["services"]
            proc = subprocess.Popen(
                cmd, cwd=DOCKER_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                if line.strip():
                    log(job_id, f"  {line.rstrip()[:160]}")
            proc.wait()
            if proc.returncode == 0:
                log(job_id, f"✓ 群組「{group['name']}」已啟動")
                jobs[job_id]["status"] = "done"
            else:
                log(job_id, f"[錯誤] 啟動失敗（exit {proc.returncode}）")
                jobs[job_id]["status"] = "failed"
        except Exception as e:
            log(job_id, f"[錯誤] {e}")
            jobs[job_id]["status"] = "failed"

    threading.Thread(target=_start, daemon=True).start()
    return jsonify({"job_id": job_id, "group": group_id})


@bp.route("/api/lab/<group_id>/stop", methods=["POST"])
def api_lab_stop(group_id: str):
    group = next((g for g in LAB_GROUPS if g["id"] == group_id), None)
    if not group:
        return jsonify({"error": "group not found"}), 404

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "logs": [], "current_step": f"stop:{group_id}"}

    def _stop():
        log(job_id, f"⏹ 停止群組「{group['name']}」...")
        try:
            cmd = ["docker", "compose", "stop"] + group["services"]
            proc = subprocess.Popen(
                cmd, cwd=DOCKER_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                if line.strip():
                    log(job_id, f"  {line.rstrip()[:160]}")
            proc.wait()
            if proc.returncode == 0:
                log(job_id, f"✓ 群組「{group['name']}」已停止")
                jobs[job_id]["status"] = "done"
            else:
                log(job_id, f"[錯誤] 停止失敗（exit {proc.returncode}）")
                jobs[job_id]["status"] = "failed"
        except Exception as e:
            log(job_id, f"[錯誤] {e}")
            jobs[job_id]["status"] = "failed"

    threading.Thread(target=_stop, daemon=True).start()
    return jsonify({"job_id": job_id, "group": group_id})


@bp.route("/api/lab/stop-all", methods=["POST"])
def api_lab_stop_all():
    """一鍵停止所有群組（休息模式）。"""
    all_services = [s for g in LAB_GROUPS for s in g["services"]]

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "logs": [], "current_step": "stop-all"}

    def _stop_all():
        log(job_id, "⏹ 停止所有服務...")
        try:
            proc = subprocess.Popen(
                ["docker", "compose", "stop"] + all_services,
                cwd=DOCKER_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                if line.strip():
                    log(job_id, f"  {line.rstrip()[:160]}")
            proc.wait()
            log(job_id, "✓ 所有服務已停止，系統進入休息模式")
            jobs[job_id]["status"] = "done"
        except Exception as e:
            log(job_id, f"[錯誤] {e}")
            jobs[job_id]["status"] = "failed"

    threading.Thread(target=_stop_all, daemon=True).start()
    return jsonify({"job_id": job_id})


@bp.route("/api/lab/start-all", methods=["POST"])
def api_lab_start_all():
    """一鍵啟動所有群組（作業模式）。"""
    body = request.get_json(force=True, silent=True) or {}
    # 可選：只啟動指定群組 ids，預設全部
    group_ids  = body.get("groups") or [g["id"] for g in LAB_GROUPS]
    groups     = [g for g in LAB_GROUPS if g["id"] in group_ids]
    services   = [s for g in groups for s in g["services"]]

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "logs": [], "current_step": "start-all"}

    def _start_all():
        log(job_id, f"▶ 啟動 {len(groups)} 個群組，共 {len(services)} 個服務...")
        try:
            proc = subprocess.Popen(
                ["docker", "compose", "up", "-d", "--no-recreate"] + services,
                cwd=DOCKER_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                if line.strip():
                    log(job_id, f"  {line.rstrip()[:160]}")
            proc.wait()
            if proc.returncode == 0:
                log(job_id, "✓ 所有服務已啟動，可以開始作業")
                jobs[job_id]["status"] = "done"
            else:
                log(job_id, f"[錯誤] 部分服務啟動失敗（exit {proc.returncode}）")
                jobs[job_id]["status"] = "failed"
        except Exception as e:
            log(job_id, f"[錯誤] {e}")
            jobs[job_id]["status"] = "failed"

    threading.Thread(target=_start_all, daemon=True).start()
    return jsonify({"job_id": job_id})
