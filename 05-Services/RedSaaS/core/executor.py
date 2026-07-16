"""套組 YAML 執行引擎 — 依序執行 preset 的每個 step。"""
from __future__ import annotations
import subprocess
import yaml
from datetime import datetime
from urllib.parse import urlparse

from core.config import PRESETS_DIR
from core.job_store import jobs, log
from core.kafka import kafka_produce
from core.defectdojo import auto_login


PRESET_ID_MAP = {
    "recon":    "quick-recon",
    "web":      "web-pentest",
    "apt":      "apt-simulation",
    "redblue":  "red-blue-exercise",
    "scb-full": "scb-full",
}


def load_preset(preset_id: str) -> dict:
    filename = PRESET_ID_MAP.get(preset_id, preset_id)
    path = PRESETS_DIR / f"{filename}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"preset not found: {preset_id}")
    with open(path) as f:
        return yaml.safe_load(f)


def run_preset_job(job_id: str, preset_id: str, target: str,
                   name: str, with_report: bool) -> None:
    """主執行迴圈：按 YAML step 順序呼叫對應 engine。"""
    # 延遲 import 避免循環
    from engines.docker_engine import run_docker_step
    from engines.zap_engine    import run_zap
    from engines.api_engine    import run_api_import
    from engines.report_engine import run_report

    jobs[job_id]["status"] = "running"
    try:
        preset = load_preset(preset_id)
    except FileNotFoundError as e:
        log(job_id, f"[錯誤] {e}")
        jobs[job_id]["status"] = "failed"
        return

    topic = preset.get("kafka_topic", "redsaas-events")
    steps = preset.get("steps", [])
    log(job_id, f"套組「{preset['name']}」開始執行，目標：{target}，共 {len(steps)} 步驟")

    if "://" not in target:
        target = f"https://{target}"
    parsed      = urlparse(target)
    target_host = parsed.hostname or target

    auth_token: str | None = None
    auth_cfg = preset.get("auth")
    if auth_cfg:
        log(job_id, "  自動登入取 token...")
        auth_token = auto_login(target, auth_cfg)
        log(job_id, "  ✓ 登入成功" if auth_token else "  [警告] 登入失敗，使用未認證模式繼續")

    kafka_produce(topic, {
        "event": "job.start", "job_id": job_id,
        "preset": preset_id, "target": target,
        "timestamp": datetime.now().isoformat(),
    })

    for i, step in enumerate(steps):
        sid        = step.get("id", f"step-{i}")
        sname      = step.get("name", sid)
        engine     = step.get("engine", "docker")
        kafka_event= step.get("kafka_event", f"{preset_id}.{sid}.done")
        blue_alert = step.get("blue_alert", "")

        log(job_id, f"[{i+1}/{len(steps)}] {sname} 開始...")
        jobs[job_id]["current_step"] = sid

        kafka_produce(topic, {
            "event": "step.start", "job_id": job_id,
            "step": sid, "name": sname,
            "timestamp": datetime.now().isoformat(),
        })
        if blue_alert:
            kafka_produce("redsaas-blue-alerts", {
                "event": "blue.alert", "severity": "medium",
                "message": blue_alert.replace("{target}", target),
                "timestamp": datetime.now().isoformat(),
            })

        try:
            result: dict = {}

            if engine == "docker":
                result = run_docker_step(
                    job_id, step, target, target_host, auth_token, jobs
                )

            elif engine == "scb":
                import scb_client  # 延遲 import，避免 K8s SDK 在啟動時 block
                scan_type = step.get("scan_type", "nmap")
                params    = step.get("parameters", [])
                log(job_id, f"  提交 SCB Scan: {scan_type}")
                try:
                    scb_result = scb_client.submit_scan(scan_type, target, params)
                    result = {"ok": True, "scan": scb_result}
                    log(job_id, f"  SCB scan 已提交: {scb_result.get('name','')}")
                except Exception as e:
                    log(job_id, f"  [警告] SCB 提交失敗: {e}")
                    result = {"ok": False}

            elif engine == "zap":
                r = run_zap(job_id, target)
                if r.get("output_path"):
                    jobs[job_id]["zap_output"] = r["output_path"]
                result = r

            elif engine == "api":
                if step.get("action") == "import_findings":
                    result = run_api_import(job_id, jobs)

            elif engine == "report":
                if with_report:
                    result = run_report(job_id, target, jobs)
                else:
                    log(job_id, "  跳過報告生成")
                    result = {"ok": True, "skipped": True}

            elif engine in ("sliver", "bloodhound", "kafka"):
                log(job_id, f"  [{engine}] 模擬執行（尚未串接真實 API）")
                result = {"ok": True, "mock": True}

            else:
                log(job_id, f"  未知引擎 {engine}，略過")
                result = {"ok": True, "skipped": True}

            status = "done" if result.get("ok") else "failed"
            log(job_id, f"[{i+1}/{len(steps)}] {sname} → {status}")
            kafka_produce(topic, {
                "event": kafka_event, "job_id": job_id,
                "step": sid, "status": status,
                "timestamp": datetime.now().isoformat(),
            })

        except subprocess.TimeoutExpired:
            log(job_id, f"[{i+1}/{len(steps)}] {sname} → 逾時，繼續下一步")
            kafka_produce(topic, {"event": kafka_event, "step": sid, "status": "timeout"})
        except Exception as e:
            log(job_id, f"[{i+1}/{len(steps)}] {sname} → 錯誤：{str(e)[:100]}")
            kafka_produce(topic, {"event": kafka_event, "step": sid, "status": "error"})

    jobs[job_id]["status"] = "done"
    kafka_produce(topic, {
        "event": "job.done", "job_id": job_id,
        "preset": preset_id, "timestamp": datetime.now().isoformat(),
    })
    log(job_id, f"=== 套組「{preset['name']}」執行完成 ===")
