#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloudflare DNS 查詢量統計腳本
帳號：infa-tech@568win.com
功能：抓取該帳號下所有 Zone 的 DNS 查詢量，輸出 CSV

認證方式：Global API Key（X-Auth-Email + X-Auth-Key）
API：GraphQL dnsAnalyticsAdaptiveGroups（優先）/ REST 備援

執行：
    python3 cloudflare_dns_analytics.py
    python3 cloudflare_dns_analytics.py --days 7      # 指定天數（Free Plan 最多 7 天）
    python3 cloudflare_dns_analytics.py --output dns_report.csv
"""

import argparse
import datetime
import json
import os
import sys
import time
import random
import logging

import requests
import pandas as pd

# ──────────────────────────────────────────────────────────────
# 設定
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# 強制繞過系統 Proxy（Cursor IDE / VPN 環境常見問題）
for _pvar in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(_pvar, None)

CF_API = "https://api.cloudflare.com/client/v4"


def load_accounts() -> list:
    """
    從環境變數 CF_ACCOUNTS_JSON 讀取多帳號設定。
    格式：[{"email":"...","api_key":"..."},  ...]
    若未設定，回傳空清單。
    """
    raw = os.environ.get("CF_ACCOUNTS_JSON", "")
    if not raw:
        logger.error("未設定 CF_ACCOUNTS_JSON 環境變數，請先 source .env")
        sys.exit(1)
    try:
        accounts = json.loads(raw)
        if not isinstance(accounts, list):
            raise ValueError("CF_ACCOUNTS_JSON 必須是 JSON 陣列")
        return accounts
    except Exception as e:
        logger.error(f"CF_ACCOUNTS_JSON 解析失敗：{e}")
        sys.exit(1)


def make_headers(account: dict) -> dict:
    """依帳號設定建立 HTTP headers"""
    return {
        "X-Auth-Email": account["email"],
        "X-Auth-Key":   account["api_key"],
        "Content-Type": "application/json",
    }

# ──────────────────────────────────────────────────────────────
# 工具函式
# ──────────────────────────────────────────────────────────────

def retry(func, *args, max_retries: int = 3, base_backoff: float = 5.0, **kwargs):
    """指數退避重試裝飾器（函式版）"""
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if attempt == max_retries:
                raise
            wait = base_backoff * (2 ** (attempt - 1)) + random.uniform(0, 2)
            logger.warning(f"第 {attempt} 次失敗：{exc}，{wait:.1f}s 後重試…")
            time.sleep(wait)


def cf_get(path: str, headers: dict, params: dict = None) -> dict:
    """GET 請求，自動處理錯誤"""
    resp = requests.get(f"{CF_API}{path}", headers=headers, params=params, timeout=30, proxies={"http": None, "https": None})
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"API 錯誤：{data.get('errors')}")
    return data


def cf_graphql(query: str, headers: dict) -> dict:
    """GraphQL 請求"""
    resp = requests.post(
        f"{CF_API}/graphql",
        headers=headers,
        json={"query": query},
        timeout=60,
        proxies={"http": None, "https": None},
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise RuntimeError(f"GraphQL 錯誤：{data['errors']}")
    return data


# ──────────────────────────────────────────────────────────────
# Step 1：取得所有 Zone
# ──────────────────────────────────────────────────────────────

def get_all_zones(headers: dict, email: str) -> list[dict]:
    """列出帳號下所有 Zone，回傳 [{id, name, plan_name}, ...]"""
    logger.info(f"取得 {email} 的所有 Zone…")
    zones = []
    page = 1
    while True:
        data = retry(cf_get, "/zones", headers, params={"page": page, "per_page": 50})
        results = data["result"]
        for z in results:
            zones.append({
                "id":        z["id"],
                "name":      z["name"],
                "status":    z["status"],
                "plan_name": z.get("plan", {}).get("name", "Unknown"),
            })
        info = data["result_info"]
        logger.info(f"  第 {page}/{info['total_pages']} 頁，累計 {len(zones)} 個 Zone")
        if page >= info["total_pages"]:
            break
        page += 1
        time.sleep(0.3)
    return zones


# ──────────────────────────────────────────────────────────────
# Step 2：取得單一 Zone 的 DNS 查詢量
# ──────────────────────────────────────────────────────────────

def _query_days_for_plan(plan_name: str, requested_days: int) -> int:
    """
    依 Plan 回傳實際可查天數（Cloudflare 官方限制）
      Free:       7 天（GraphQL 限制）
      Pro:        30 天
      Business:   30 天
      Enterprise: 30 天
    """
    plan_lower = plan_name.lower()
    if "free" in plan_lower:
        allowed = 7
    else:
        allowed = 30
    actual = min(requested_days, allowed)
    if actual < requested_days:
        logger.debug(f"  Plan={plan_name}，限制 {allowed} 天，調整為 {actual} 天")
    return actual


def get_dns_query_count_graphql(zone_id: str, start_date: str, end_date: str, headers: dict) -> int:
    """
    GraphQL dnsAnalyticsAdaptiveGroups 查 DNS 總查詢量
    start_date / end_date 格式：YYYY-MM-DD
    """
    query = f"""
    query {{
      viewer {{
        zones(filter: {{zoneTag: \"{zone_id}\"}}) {{
          dnsAnalyticsAdaptiveGroups(
            limit: 1000
            filter: {{
              date_geq: \"{start_date}\"
              date_leq: \"{end_date}\"
            }}
            orderBy: [date_ASC]
          ) {{
            dimensions {{ date }}
            count
          }}
        }}
      }}
    }}
    """
    data = cf_graphql(query, headers)
    groups = (
        data.get("data", {})
            .get("viewer", {})
            .get("zones", [{}])[0]
            .get("dnsAnalyticsAdaptiveGroups", [])
    )
    total = sum(g.get("count", 0) or 0 for g in groups)
    return total


def get_dns_query_count_rest(zone_id: str, since_iso: str, until_iso: str, headers: dict) -> int:
    """
    REST /zones/{zone_id}/dns_analytics/report 備援查詢
    since / until 格式：YYYY-MM-DDTHH:MM:SSZ
    """
    data = retry(
        cf_get,
        f"/zones/{zone_id}/dns_analytics/report",
        headers,
        params={"metrics": "queryCount", "since": since_iso, "until": until_iso},
    )
    result = data.get("result", {})
    totals = result.get("totals", {})
    if "queryCount" in totals:
        return int(totals["queryCount"] or 0)
    total = 0
    for row in result.get("data", []):
        m = row.get("metrics")
        if isinstance(m, list) and m:
            total += int(m[0] or 0)
        elif isinstance(m, dict):
            total += int(m.get("queryCount", 0) or 0)
    return total


def get_zone_dns_queries(zone: dict, requested_days: int, headers: dict, email: str) -> dict:
    """
    取得單一 Zone 的 DNS 查詢量，先嘗試 GraphQL，失敗則用 REST。
    """
    zone_id   = zone["id"]
    zone_name = zone["name"]
    plan_name = zone["plan_name"]

    actual_days = _query_days_for_plan(plan_name, requested_days)

    today      = datetime.date.today()
    end_date   = today
    start_date = today - datetime.timedelta(days=actual_days - 1)

    start_str  = start_date.strftime("%Y-%m-%d")
    end_str    = end_date.strftime("%Y-%m-%d")
    date_range = f"{start_str} ~ {end_str}（{actual_days} 天）"

    dns_count = None
    method    = None

    # ── 優先：GraphQL ─────────────────────────────────────────
    try:
        dns_count = retry(get_dns_query_count_graphql, zone_id, start_str, end_str, headers)
        method = "GraphQL"
    except Exception as exc:
        logger.warning(f"  [{zone_name}] GraphQL 失敗：{exc}，改用 REST…")

    # ── 備援：REST ────────────────────────────────────────────
    if dns_count is None:
        try:
            now       = datetime.datetime.now(datetime.timezone.utc)
            since_dt  = now - datetime.timedelta(days=actual_days)
            since_iso = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            until_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            dns_count = retry(get_dns_query_count_rest, zone_id, since_iso, until_iso, headers)
            method    = "REST"
        except Exception as exc:
            logger.error(f"  [{zone_name}] REST 也失敗：{exc}")
            dns_count = None
            method    = "ERROR"

    return {
        "帳號":     email,
        "Zone":     zone_name,
        "狀態":     zone["status"],
        "計劃":     plan_name,
        "DNS查詢量": dns_count if dns_count is not None else "N/A",
        "查詢區間":  date_range,
        "查詢方式":  method,
    }


# ──────────────────────────────────────────────────────────────
# 主程式
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cloudflare DNS 查詢量統計")
    parser.add_argument(
        "--days", type=int, default=7,
        help="查詢天數（Free Plan 最多 7 天，預設 7）",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="輸出 CSV 路徑（預設：dns_analytics_YYYYMMDD_HHMMSS.csv）",
    )
    args = parser.parse_args()

    timestamp  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = args.output or f"dns_analytics_{timestamp}.csv"

    print("=" * 60)
    print("  Cloudflare DNS 查詢量統計（多帳號）")
    print(f"  天數 : {args.days} 天")
    print(f"  輸出 : {output_csv}")
    print("=" * 60)

    # 載入所有帳號
    accounts = load_accounts()
    print(f"  帳號數：{len(accounts)} 個\n")

    all_rows = []

    # 逐帳號處理
    for acct in accounts:
        email   = acct.get("email", "unknown")
        headers = make_headers(acct)

        print(f"\n{'─'*60}")
        print(f"  帳號：{email}")
        print(f"{'─'*60}")

        # Step 1：取得該帳號所有 Zone
        try:
            zones = get_all_zones(headers, email)
        except Exception as e:
            logger.error(f"[{email}] 取得 Zone 失敗：{e}")
            continue

        print(f"  找到 {len(zones)} 個 Zone，開始查詢…\n")

        # Step 2：逐一查詢
        for i, zone in enumerate(zones, 1):
            logger.info(f"[{i}/{len(zones)}] {zone['name']} ({zone['plan_name']})")
            row = get_zone_dns_queries(zone, args.days, headers, email)
            all_rows.append(row)

            count_display = (
                f"{row['DNS查詢量']:,}" if isinstance(row['DNS查詢量'], int) else row['DNS查詢量']
            )
            status_icon = "✅" if row["查詢方式"] not in ("ERROR", None) else "❌"
            print(f"  {status_icon} {zone['name']:<35} {count_display:>12} 次  [{row['查詢方式']}]")

            time.sleep(0.3)   # 避免速率限制

    if not all_rows:
        print("\n[WARN] 沒有任何資料，請確認帳號設定。")
        return

    # Step 3：輸出 CSV
    df = pd.DataFrame(all_rows)

    # 加入合計列
    total_count = df["DNS查詢量"].apply(
        lambda x: x if isinstance(x, int) else 0
    ).sum()
    total_row = {
        "帳號":     f"【{len(accounts)} 個帳號合計】",
        "Zone":     "【合計】",
        "狀態":     "-",
        "計劃":     "-",
        "DNS查詢量": total_count,
        "查詢區間":  f"（{args.days} 天）",
        "查詢方式":  "-",
    }
    df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    # Step 4：摘要輸出
    print("\n" + "=" * 60)
    print("📊 查詢完成")
    print("=" * 60)
    print(df[["帳號", "Zone", "計劃", "DNS查詢量", "查詢區間"]].to_string(index=False))
    print("\n" + "-" * 60)
    print(f"  總 DNS 查詢量：{total_count:,} 次")
    print(f"  總 Zone 數：{len(all_rows)} 個")
    print(f"  結果已儲存至：{output_csv}")
    print("=" * 60)


if __name__ == "__main__":
    main()
