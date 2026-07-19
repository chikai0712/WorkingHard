"""DefectDojo 輔助函式：自動建立 product / engagement。"""
from __future__ import annotations
from datetime import datetime
import requests
from core.config import DD_URL, DD_TOKEN


def _headers() -> dict:
    return {"Authorization": f"Token {DD_TOKEN}", "Content-Type": "application/json"}


def create_engagement(job_id: str, name: str, target: str) -> int | None:
    """找或建立 product，然後建立 engagement，回傳 engagement id。"""
    try:
        h = _headers()
        r = requests.get(
            f"{DD_URL}/api/v2/products/?name={requests.utils.quote(name)}&limit=1",
            headers=h, timeout=10,
        )
        results = r.json().get("results", [])
        if results:
            product_id = results[0]["id"]
        else:
            r2 = requests.post(
                f"{DD_URL}/api/v2/products/", headers=h, timeout=10,
                json={"name": name, "description": f"RedSaaS 自動建立：{target}", "prod_type": 1},
            )
            product_id = r2.json()["id"]

        today = datetime.now().strftime("%Y-%m-%d")
        r3 = requests.post(
            f"{DD_URL}/api/v2/engagements/", headers=h, timeout=10,
            json={
                "name": f"RedSaaS {today}",
                "product": product_id,
                "target_start": today,
                "target_end": today,
                "engagement_type": "CI/CD",
                "status": "In Progress",
            },
        )
        return r3.json().get("id")
    except Exception:
        return None


def auto_login(target: str, auth: dict) -> str | None:
    """依 YAML auth 設定自動登入，回傳 JWT token。"""
    try:
        login_url = auth.get("login_url", "").replace("{target}", target)
        payload = dict(auth.get("body", {}))
        resp = requests.post(login_url, json=payload, timeout=10)
        data = resp.json()
        for key in auth.get("token_field", "token").split("."):
            data = data.get(key, {}) if isinstance(data, dict) else None
        return str(data) if data else None
    except Exception:
        return None
