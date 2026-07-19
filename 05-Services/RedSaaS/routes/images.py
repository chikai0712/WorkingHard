"""routes/images.py — Docker Image 倉庫管理：查詢狀態、pull 單個、pull 全部。"""
from __future__ import annotations
import subprocess
import threading
import uuid

from flask import Blueprint, jsonify

from core.job_store import jobs, log
from core.image_catalog import IMAGE_CATALOG

bp = Blueprint("images", __name__)


def _image_info(image: str, tag: str) -> dict:
    try:
        r = subprocess.run(
            ["docker", "image", "inspect", f"{image}:{tag}",
             "--format", "{{.Id}}|{{.Size}}|{{.Created}}"],
            capture_output=True, text=True, timeout=8,
        )
        if r.returncode != 0:
            return {"present": False}
        parts = r.stdout.strip().split("|")
        return {
            "present": True,
            "digest":  parts[0][:19] if parts else "",
            "size_mb": round(int(parts[1]) / 1024 / 1024, 1) if len(parts) > 1 else 0,
            "created": parts[2][:10] if len(parts) > 2 else "",
        }
    except Exception:
        return {"present": False}


@bp.route("/api/images")
def api_images():
    return jsonify([{**item, **_image_info(item["image"], item["tag"])}
                    for item in IMAGE_CATALOG])


@bp.route("/api/images/<image_id>/pull", methods=["POST"])
def api_image_pull(image_id: str):
    item = next((x for x in IMAGE_CATALOG if x["id"] == image_id), None)
    if not item:
        return jsonify({"error": "image not found"}), 404

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "logs": [], "current_step": image_id}
    full   = f"{item['image']}:{item['tag']}"

    def _pull():
        log(job_id, f"開始 pull {full}...")
        proc = subprocess.Popen(["docker", "pull", full],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1)
        for line in proc.stdout:
            if line.strip():
                log(job_id, f"  {line.rstrip()[:160]}")
        proc.wait()
        if proc.returncode == 0:
            info = _image_info(item["image"], item["tag"])
            log(job_id, f"✓ Pull 完成：{full}（{info.get('size_mb', '?')} MB）")
            jobs[job_id]["status"] = "done"
        else:
            log(job_id, f"[錯誤] Pull 失敗：{full}")
            jobs[job_id]["status"] = "failed"

    threading.Thread(target=_pull, daemon=True).start()
    return jsonify({"job_id": job_id, "image": full})


@bp.route("/api/images/pull-all", methods=["POST"])
def api_images_pull_all():
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "logs": [], "current_step": "pull-all"}

    def _pull_all():
        total = len(IMAGE_CATALOG)
        for i, item in enumerate(IMAGE_CATALOG, 1):
            full = f"{item['image']}:{item['tag']}"
            log(job_id, f"[{i}/{total}] Pull {full}...")
            proc = subprocess.Popen(["docker", "pull", full],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
            for line in proc.stdout:
                if line.strip():
                    log(job_id, f"  {line.rstrip()[:120]}")
            proc.wait()
            log(job_id, f"  {'✓' if proc.returncode == 0 else '✘ 失敗'} {full}")
        jobs[job_id]["status"] = "done"
        log(job_id, "=== 全部 Pull 完成 ===")

    threading.Thread(target=_pull_all, daemon=True).start()
    return jsonify({"job_id": job_id})
