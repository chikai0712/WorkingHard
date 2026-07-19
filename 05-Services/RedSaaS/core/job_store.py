"""Jobs 狀態字典與 log 輔助函式。所有 engine / route 都從這裡 import。"""
from __future__ import annotations
from datetime import datetime

jobs: dict[str, dict] = {}


def log(job_id: str, msg: str) -> None:
    jobs[job_id]["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def get_job(job_id: str) -> dict | None:
    return jobs.get(job_id)


def new_job(job_id: str, initial: dict) -> None:
    jobs[job_id] = initial
