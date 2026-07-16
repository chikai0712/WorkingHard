"""docker engine — 執行 YAML step 裡的 docker run 指令。"""
from __future__ import annotations
import shlex
import subprocess
import threading
from pathlib import Path

from core.job_store import log
from core.defectdojo import create_engagement


def run_docker_step(job_id: str, step: dict, target: str, target_host: str,
                    auth_token: str | None, jobs: dict) -> dict:
    cmd_tpl = step.get("cmd", "")
    cmd_str = (cmd_tpl
               .replace("{target}", target)
               .replace("{target_host}", target_host)
               .replace("{job_id}", job_id)
               .replace("{token}", auth_token or "")
               .strip())
    cmd = shlex.split(cmd_str)
    timeout = step.get("timeout", 300)

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    output_lines: list[str] = []
    deadline = [False]

    timer = threading.Timer(timeout, lambda: (proc.kill(), deadline.__setitem__(0, True)))
    timer.start()
    try:
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                output_lines.append(line)
                log(job_id, f"  {line[:200]}")
        proc.wait()
    finally:
        timer.cancel()

    if deadline[0]:
        raise subprocess.TimeoutExpired(cmd, timeout)

    # 記錄各工具輸出路徑，供 api_engine 匯入 DefectDojo
    nuclei_out  = f"/tmp/nuclei-{job_id}.jsonl"
    gobuster_out = f"/tmp/gobuster-{job_id}.txt"

    if Path(nuclei_out).exists():
        jobs[job_id]["last_scan_output"] = nuclei_out
        if not jobs[job_id].get("dd_engagement_id"):
            eng_id = create_engagement(
                job_id,
                jobs[job_id].get("name", target),
                target,
            )
            if eng_id:
                jobs[job_id]["dd_engagement_id"] = eng_id
                log(job_id, f"  DefectDojo engagement 已建立：#{eng_id}")

    if Path(gobuster_out).exists() and Path(gobuster_out).stat().st_size > 0:
        jobs[job_id]["gobuster_output"] = gobuster_out

    return {"ok": proc.returncode == 0, "output": "\n".join(output_lines[-20:])}
