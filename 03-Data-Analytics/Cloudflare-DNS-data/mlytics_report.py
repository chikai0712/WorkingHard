#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mlytics 數據收集腳本
功能：從 Mlytics 收集域名統計數據（DNS 查詢、CDN 流量等）並匯出為 CSV
參考 Cloudflare 腳本格式，保持輸出格式一致
"""

import requests
import pandas as pd
import datetime
import json
import time
import random
import os
import sys

# ============================================
# Mlytics API 配置
# ============================================
# 注意：請根據 Mlytics 實際 API 文檔更新以下配置
# 
# Mlytics API 認證方式（常見的幾種方式）：
# 1. API Key + API Secret
# 2. Bearer Token
# 3. OAuth 2.0
# 
# 請根據 Mlytics 實際文檔選擇正確的認證方式

# Mlytics API 基礎 URL（根據測試結果更新）
MLYTICS_API_BASE_URL = "https://api.mlytics.com"  # 正確的 Base URL（不需要 /v1）

# Mlytics 帳戶認證資訊
# 注意：如果 Mlytics 只需要 API Key（不需要 Secret），請在 get_mlytics_headers 函數中調整認證方式
MLYTICS_API_KEY = "wcHGixTn6JFE7C5XVI0yJgfFWlbzeJERfSqkRHfCP2lze7oJEv"
MLYTICS_API_SECRET = ""  # 如果 Mlytics 不需要 Secret，可以留空

# 方式 2: Bearer Token（如果使用 Bearer Token，請使用此方式）
# MLYTICS_BEARER_TOKEN = "your_bearer_token_here"

# 多個帳戶的認證信息列表
accounts = [
    {
        "account_id": "ck.chiu@unition.global",
        "api_key": MLYTICS_API_KEY,
        "api_secret": MLYTICS_API_SECRET,  # 如果不需要 Secret，可以設為空字串
        "email": "ck.chiu@unition.global"
    },
    # 可以添加更多帳戶
    # {
    #     "account_id": "account_2",
    #     "api_key": "api_key_2",
    #     "api_secret": "api_secret_2",
    #     "email": "user2@example.com"
    # }
]

# 依 account_id 快速查找帳戶資訊
account_map = {acc["account_id"]: acc for acc in accounts}

# 計算日期範圍：過去 7 天
end_date = datetime.datetime.now(datetime.timezone.utc).date()
start_date = end_date - datetime.timedelta(days=7)
start_datetime = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=datetime.timezone.utc)
end_datetime = datetime.datetime.combine(end_date, datetime.time.min, tzinfo=datetime.timezone.utc)

print("="*60)
print("🚀 Mlytics 數據收集腳本啟動")
print("="*60)
print(f"📅 查詢日期範圍：{start_date} 至 {end_date}")
print(f"📋 帳戶數量：{len(accounts)}")
print(f"🌐 API Base URL: {MLYTICS_API_BASE_URL}")
print("="*60)

# 記錄因速率限制而失敗的請求
rate_limited_requests = []

# 記錄所有失敗的域名及原因
failed_domains = []

# 記錄需要重試的失敗域名
failed_zones_to_retry = []

# 自定義異常：用於跳過不支援的域名
class SkipZone(Exception):
    """非致命錯誤，用於跳過不支援的域名"""
    pass

# ============================================
# API 認證函數
# ============================================
def get_mlytics_headers(account):
    """
    獲取 Mlytics API 請求頭
    
    根據 Mlytics API 文檔，可能需要以下認證方式之一：
    1. API Key + Secret (Basic Auth 或 Header)
    2. Bearer Token
    3. OAuth 2.0
    
    請根據實際 API 文檔修改此函數
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # 方式 1: 使用 API Key only（Header 方式）- 當前配置
    # 注意：目前只使用 API Key，如果 Mlytics 需要 Secret，請取消下面的註解
    if "api_key" in account and account["api_key"]:
        # Mlytics API Key 認證（請根據實際 API 文檔調整 Header 名稱）
        headers["X-API-Key"] = account["api_key"]
        # 或者可能是其他 Header 名稱：
        # headers["Authorization"] = f"API-Key {account['api_key']}"
        # headers["apikey"] = account["api_key"]
    
    # 方式 2: 使用 API Key + Secret（如果 Mlytics 需要 Secret）
    if "api_key" in account and "api_secret" in account and account.get("api_secret"):
        headers["X-API-Key"] = account["api_key"]
        headers["X-API-Secret"] = account["api_secret"]
        # 或者使用 Basic Auth:
        # import base64
        # credentials = f"{account['api_key']}:{account['api_secret']}"
        # encoded = base64.b64encode(credentials.encode()).decode()
        # headers["Authorization"] = f"Basic {encoded}"
    
    # 方式 3: 使用 Bearer Token
    # if "bearer_token" in account:
    #     headers["Authorization"] = f"Bearer {account['bearer_token']}"
    
    return headers

# ============================================
# 重試函數 - 處理速率限制
# ============================================
def retry_with_backoff(func, *args, max_retries=3, initial_backoff=10, domain_info=None, **kwargs):
    retries = 0
    while retries < max_retries:
        try:
            result = func(*args, **kwargs)
            return result, True  # 成功，返回結果和成功標誌
        except Exception as e:
            error_message = str(e).lower()
            # 檢查是否為速率限制錯誤
            if "rate limiter budget depleted" in error_message or "rate limit" in error_message or "429" in error_message:
                retries += 1
                if retries < max_retries:
                    # 計算退避時間 (指數退避 + 隨機抖動)
                    backoff_time = initial_backoff * (2 ** (retries - 1)) + random.uniform(1, 5)
                    print(f"遇到速率限制，等待 {backoff_time:.2f} 秒後重試 ({retries}/{max_retries})...")
                    time.sleep(backoff_time)
                else:
                    print(f"達到最大重試次數，將在稍後重試")
                    if domain_info:
                        domain_info["失敗原因"] = f"速率限制 - {error_message}"
                        failed_domains.append(domain_info.copy())
                    return None, False  # 標記為需要稍後重試
            else:
                # 其他錯誤，返回None但不標記為稍後重試
                print(f"遇到非速率限制錯誤: {str(e)}")
                if domain_info:
                    domain_info["失敗原因"] = f"一般錯誤 - {str(e)}"
                    failed_domains.append(domain_info.copy())
                return None, True
    return None, True

# ============================================
# 獲取所有域名列表
# ============================================
def get_all_zones(account, limit=None):
    """
    獲取 Mlytics 帳戶中的所有域名列表
    
    注意：此函數需要根據 Mlytics 實際 API 文檔進行調整
    常見的 API 端點可能是：
    - GET /domains
    - GET /zones
    - GET /projects/{project_id}/domains
    """
    account_id = account["account_id"]
    headers = get_mlytics_headers(account)
    
    print(f"正在獲取帳戶 {account_id} 的所有域名列表...")
    
    zones = []
    page = 1
    per_page = 50
    
    # 根據 Mlytics API 文檔調整端點和參數
    # 範例端點（請根據實際 API 文檔修改）：
    url = f"{MLYTICS_API_BASE_URL}/domains"  # 或 /zones, /projects/{id}/domains
    
    while True:
        try:
            params = {
                "page": page,
                "per_page": per_page,
                # 可能還需要其他參數，如 account_id, project_id 等
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # 檢查 HTTP 狀態碼
            if response.status_code == 401:
                raise Exception("認證失敗，請檢查 API Key 和 Secret")
            elif response.status_code == 403:
                raise Exception("無權限訪問此資源")
            elif response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                raise Exception(error_msg)
            
            data = response.json()
            
            # 根據 Mlytics API 響應格式調整（可能是 data, results, domains 等）
            # 範例響應格式（請根據實際 API 文檔修改）：
            if isinstance(data, dict):
                results = data.get("data", data.get("results", data.get("domains", [])))
            elif isinstance(data, list):
                results = data
            else:
                results = []
            
            # 為每個結果添加帳戶信息
            for zone in results:
                zone["account_id"] = account_id
                zone["account_email"] = account.get("email", account_id)
            
            zones.extend(results)
            
            if limit and len(zones) >= limit:
                zones = zones[:limit]
                break
            
            # 檢查是否還有更多頁面
            # 根據 Mlytics API 響應格式調整（可能是 has_more, next_page 等）
            if isinstance(data, dict):
                has_more = data.get("has_more", False)
                total = data.get("total", 0)
                if not has_more or len(results) < per_page or len(zones) >= total:
                    break
            elif len(results) < per_page:
                break
                
            page += 1
            time.sleep(0.5)  # 避免觸發速率限制
            
        except Exception as e:
            print(f"獲取域名列表時出錯: {str(e)}")
            time.sleep(2)
            continue
    
    print(f"帳戶 {account_id} 找到 {len(zones)} 個域名")
    return zones

# ============================================
# 獲取域名計劃/方案類型
# ============================================
def get_zone_plan(zone_id, zone_name, account):
    """
    獲取域名的計劃/方案類型
    
    注意：Mlytics 可能沒有明確的計劃等級（如 Free/Pro），
    可能需要從其他欄位推斷（如 features, tier, plan_type 等）
    """
    account_id = account["account_id"]
    headers = get_mlytics_headers(account)
    
    print(f"正在獲取帳戶 {account_id} 的域名 {zone_name} 的方案信息...")
    
    domain_info = {
        "帳戶": account.get("email", account_id),
        "域名": zone_name,
        "zone_id": zone_id,
        "操作": "獲取方案類型",
        "失敗時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    def _get_zone_plan():
        # 根據 Mlytics API 文檔調整端點
        url = f"{MLYTICS_API_BASE_URL}/domains/{zone_id}"  # 或 /zones/{zone_id}
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"HTTP 狀態碼: {response.status_code}")
        
        data = response.json()
        
        # 根據 Mlytics API 響應格式調整
        # 可能的路徑：data.plan, data.tier, data.features, data.plan_type 等
        if isinstance(data, dict):
            domain_data = data.get("data", data)
            plan = domain_data.get("plan", domain_data.get("tier", domain_data.get("plan_type", "標準方案")))
            if plan:
                return plan
        
        return "未知方案"
    
    result, _ = retry_with_backoff(_get_zone_plan, max_retries=3, initial_backoff=5, domain_info=domain_info)
    
    if result is None:
        return "未知方案"
    
    return result

# ============================================
# 獲取 HTTP 流量指標（CDN 流量）
# ============================================
def get_zone_metric(zone_id, zone_name, metric_name, account, start_date, end_date):
    """
    獲取域名的 CDN 流量指標
    
    注意：Mlytics 主要提供 CDN 相關的統計，可能包含：
    - 總流量（bytes）
    - 緩存流量（cached_bytes）
    - 總請求數（requests）
    - 緩存請求數（cached_requests）
    
    根據 Mlytics API 文檔調整此函數
    """
    account_id = account["account_id"]
    headers = get_mlytics_headers(account)
    
    print(f"正在獲取帳戶 {account_id} 的域名 {zone_name} 的 {metric_name} 指標...")
    
    domain_info = {
        "帳戶": account.get("email", account_id),
        "域名": zone_name,
        "zone_id": zone_id,
        "操作": f"獲取{metric_name}指標",
        "失敗時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    def _get_zone_metric():
        # 根據 Mlytics API 文檔調整端點和參數
        # 範例端點（請根據實際 API 文檔修改）：
        url = f"{MLYTICS_API_BASE_URL}/domains/{zone_id}/analytics"  # 或 /stats, /metrics
        
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "metric": metric_name,  # 可能是 "bytes", "requests", "cached_bytes", "cached_requests"
            "granularity": "day"  # 或 "hour", "day"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=60)
        
        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("message", f"HTTP {response.status_code}")
            raise Exception(f"HTTP {response.status_code} - {error_msg}")
        
        data = response.json()
        
        # 根據 Mlytics API 響應格式調整
        # 可能的響應格式：
        # {
        #   "data": [
        #     {"date": "2025-12-10", "bytes": 1234567},
        #     ...
        #   ],
        #   "total": {"bytes": 12345678}
        # }
        
        if isinstance(data, dict):
            # 優先使用 total 欄位（總計）
            total_value = data.get("total", {}).get(metric_name, 0)
            if total_value:
                result = total_value
            else:
                # 否則從 data 陣列累加
                data_list = data.get("data", [])
                result = sum(item.get(metric_name, 0) for item in data_list)
        elif isinstance(data, list):
            result = sum(item.get(metric_name, 0) for item in data)
        else:
            result = 0
        
        # 處理度量單位轉換
        if metric_name == "bytes" or metric_name == "cached_bytes":
            # 轉換為 MB
            return round(result / (1024 * 1024), 2) if result > 0 else 0
        else:
            return result if result > 0 else 0
    
    result, need_later_retry = retry_with_backoff(_get_zone_metric, max_retries=2, initial_backoff=2, domain_info=domain_info)
    
    if result is None:
        if not need_later_retry:
            return "none"
        else:
            rate_limited_requests.append({
                "zone_id": zone_id,
                "zone_name": zone_name,
                "metric_name": metric_name,
                "account": account
            })
            return "rate_limited"
    
    return result

# ============================================
# 獲取 DNS 查詢數
# ============================================
def get_dns_query_count(zone_id, zone_name, account, plan_name=None, start_date=None, end_date=None):
    """
    獲取域名的 DNS 查詢總數
    
    根據 Mlytics API 文檔調整此函數
    """
    account_id = account["account_id"]
    headers = get_mlytics_headers(account)
    
    if start_date is None:
        start_date = start_datetime
    if end_date is None:
        end_date = end_datetime
    
    # 計算時間範圍描述（用於 CSV 輸出）
    time_diff = (end_date.date() - start_date.date()).days
    if time_diff >= 30:
        csv_time_range = "30天"
    elif time_diff >= 7:
        csv_time_range = "7天"
    elif time_diff >= 1:
        csv_time_range = f"{time_diff}天"
    else:
        csv_time_range = "24小時"
    
    domain_info = {
        "帳戶": account.get("email", account_id),
        "域名": zone_name,
        "zone_id": zone_id,
        "操作": "獲取DNS查詢數",
        "失敗時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    def _get_dns_queries():
        # 根據 Mlytics API 文檔調整端點
        url = f"{MLYTICS_API_BASE_URL}/domains/{zone_id}/dns/analytics"  # 或 /dns/stats, /dns/queries
        
        params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "metric": "query_count",  # 或 "queries", "requests"
            "granularity": "day"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=60)
        
        if response.status_code == 403:
            raise SkipZone("DNS Analytics 403 (無權限)")
        elif response.status_code == 400:
            raise SkipZone("DNS Analytics 400 (不支援)")
        elif response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
        
        data = response.json()
        
        # 根據 Mlytics API 響應格式調整
        if isinstance(data, dict):
            total = data.get("total", {}).get("query_count", data.get("total", {}).get("queries", 0))
            if total:
                return int(total)
            
            # 從 data 陣列累加
            data_list = data.get("data", [])
            total = sum(item.get("query_count", item.get("queries", 0)) for item in data_list)
        elif isinstance(data, list):
            total = sum(item.get("query_count", item.get("queries", 0)) for item in data)
        else:
            total = 0
        
        return int(total)
    
    try:
        result, need_later_retry = retry_with_backoff(_get_dns_queries, max_retries=2, initial_backoff=2, domain_info=domain_info)
        
        if result is not None:
            return (result, csv_time_range)
        else:
            domain_info["失敗原因"] = "DNS 查詢數獲取失敗"
            failed_domains.append(domain_info.copy())
            return ("N/A (查詢失敗)", csv_time_range)
    except SkipZone as e:
        skip_msg = str(e)
        print(f"  ⚠️  DNS Analytics 失敗: {skip_msg[:100]}...")
        domain_info["失敗原因"] = f"計劃限制 - {skip_msg}"
        failed_domains.append(domain_info.copy())
        return ("N/A (計劃限制)", csv_time_range)
    except Exception as e:
        error_msg = str(e)
        print(f"  ⚠️  DNS Analytics 失敗: {error_msg[:100]}...")
        domain_info["失敗原因"] = f"查詢失敗 - {error_msg}"
        failed_domains.append(domain_info.copy())
        return ("N/A (查詢失敗)", csv_time_range)

# ============================================
# 保存結果到CSV文件
# ============================================
def save_results_to_csv(results, filename, is_append=False):
    if not results:
        return
        
    df = pd.DataFrame(results)
    
    if "zone_id" in df.columns:
        df = df.drop(columns=["zone_id"])
    
    try:
        df["排序值"] = pd.to_numeric(df["總流量(MB)"], errors="coerce").fillna(-1)
        df = df.sort_values(by="排序值", ascending=False)
        df = df.drop(columns=["排序值"])
    except Exception as e:
        print(f"排序時出錯: {str(e)}")
    
    file_exists = os.path.isfile(filename)
    
    if is_append and file_exists:
        df.to_csv(filename, mode='a', index=False, header=False, encoding="utf-8-sig")
    else:
        df.to_csv(filename, index=False, encoding="utf-8-sig")
    
    print(f"數據已保存到 {filename}")

# ============================================
# 主函數
# ============================================
def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CLI 模式：單獨重新測試失敗清單
    if len(sys.argv) >= 3 and sys.argv[1] == "--retry-failed":
        failed_csv_input = sys.argv[2]
        results_csv_override = sys.argv[3] if len(sys.argv) >= 4 else f"mlytics_retry_{timestamp}.csv"
        print("重新測試功能需要根據 Mlytics API 實際情況實現")
        print(f"失敗清單: {failed_csv_input}")
        print(f"輸出檔案: {results_csv_override}")
        return
    
    # 定義輸出文件名
    results_csv = f"mlytics_metrics_{timestamp}.csv"
    failed_domains_csv = f"mlytics_failed_domains_{timestamp}.csv"
    
    print("\n開始獲取 Mlytics 帳戶的域名資訊...")
    
    all_results = []
    total_accounts = len(accounts)
    
    # 為每個帳戶獲取域名信息
    for account_idx, account in enumerate(accounts, 1):
        print(f"\n{'='*60}")
        print(f"📧 處理帳戶 [{account_idx}/{total_accounts}]: {account.get('email', account['account_id'])}")
        print(f"{'='*60}")
        
        # 獲取該帳戶的所有域名
        zones = get_all_zones(account)
        if not zones:
            print(f"帳戶 {account['account_id']} 沒有找到域名，或者獲取失敗")
            continue
        
        # 每批次處理10個域名
        batch_size = 10
        processed_count = 0
        
        for i in range(0, len(zones), batch_size):
            batch = zones[i:i+batch_size]
            print(f"\n{'='*60}")
            print(f"處理帳戶 {account['account_id']} 的第 {i+1} 到 {min(i+batch_size, len(zones))} 個域名 (共 {len(zones)} 個)")
            print(f"{'='*60}")
            
            batch_results = []
            
            for idx, zone in enumerate(batch, 1):
                # 根據 Mlytics API 響應格式調整（可能是 id, domain_id, zone_id, name, domain 等）
                zone_id = zone.get("id", zone.get("domain_id", zone.get("zone_id", "")))
                zone_name = zone.get("name", zone.get("domain", zone.get("domain_name", "未知域名")))
                global_idx = i + idx
                
                print(f"\n[{global_idx}/{len(zones)}] 處理域名: {zone_name}")
                
                try:
                    # 獲取計劃類型
                    print(f"  → 獲取方案類型...")
                    plan = get_zone_plan(zone_id, zone_name, account)
                    print(f"  → 方案: {plan}")
                    time.sleep(1)
                    
                    # 分別獲取每個指標
                    print(f"  → 獲取總流量...")
                    bytes_total = get_zone_metric(zone_id, zone_name, "bytes", account, start_datetime, end_datetime)
                    time.sleep(1)
                    
                    print(f"  → 獲取總請求數...")
                    requests_count = get_zone_metric(zone_id, zone_name, "requests", account, start_datetime, end_datetime)
                    time.sleep(1)
                    
                    print(f"  → 獲取緩存流量...")
                    cached_bytes = get_zone_metric(zone_id, zone_name, "cached_bytes", account, start_datetime, end_datetime)
                    time.sleep(1)
                    
                    print(f"  → 獲取緩存請求數...")
                    cached_requests = get_zone_metric(zone_id, zone_name, "cached_requests", account, start_datetime, end_datetime)
                    time.sleep(1)
                    
                    print(f"  → 獲取DNS查詢數...")
                    dns_queries_result = get_dns_query_count(zone_id, zone_name, account, plan, start_datetime, end_datetime)
                    if isinstance(dns_queries_result, tuple):
                        dns_queries, dns_time_range = dns_queries_result
                    else:
                        dns_queries = dns_queries_result
                        dns_time_range = "未知"
                    time.sleep(1)
                    
                    batch_results.append({
                        "帳戶": account.get("email", account["account_id"]),
                        "域名": zone_name,
                        "狀態": zone.get("status", zone.get("state", "未知")),
                        "計劃": plan,
                        "總請求數": requests_count,
                        "總流量(MB)": bytes_total,
                        "緩存流量(MB)": cached_bytes,
                        "緩存請求數": cached_requests,
                        "DNS查詢數": dns_queries,
                        "DNS查詢時間範圍": dns_time_range,
                        "失敗原因": "",
                        "zone_id": zone_id
                    })
                    
                    print(f"  ✅ 域名 {zone_name} 處理完成")
                    processed_count += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"  ❌ 域名 {zone_name} 處理失敗: {error_msg}")
                    failed_zones_to_retry.append({
                        "zone": zone,
                        "zone_id": zone_id,
                        "zone_name": zone_name,
                        "account": account,
                        "error": error_msg,
                        "retry_count": 0
                    })
                    batch_results.append({
                        "帳戶": account.get("email", account["account_id"]),
                        "域名": zone_name,
                        "狀態": zone.get("status", zone.get("state", "未知")),
                        "計劃": "獲取失敗",
                        "總請求數": "錯誤",
                        "總流量(MB)": "錯誤",
                        "緩存流量(MB)": "錯誤",
                        "緩存請求數": "錯誤",
                        "DNS查詢數": "錯誤",
                        "DNS查詢時間範圍": "錯誤",
                        "失敗原因": error_msg,
                        "zone_id": zone_id
                    })
            
            # 添加批次結果到總結果
            all_results.extend(batch_results)
            
            # 每處理 10 筆就寫入一次
            if len(all_results) == len(batch_results):
                save_results_to_csv(batch_results, results_csv, is_append=False)
                print(f"\n💾 已保存第一批 {len(batch_results)} 筆數據到 {results_csv}")
            else:
                save_results_to_csv(batch_results, results_csv, is_append=True)
                print(f"\n💾 已追加 {len(batch_results)} 筆數據到 {results_csv} (累計: {len(all_results)} 筆)")
            
            # 每批次處理完後休息一下
            if i + batch_size < len(zones):
                print(f"\n⏸️  批次處理完成，休息20秒避免速率限制...")
                time.sleep(20)
        
        # 每個帳戶處理完成後休息更長時間
        if account != accounts[-1]:
            print(f"帳戶 {account['account_id']} 處理完成，休息60秒後處理下一個帳戶...")
            time.sleep(60)
    
    # 按 Plan 分組統計總計（與 Cloudflare 腳本相同）
    print("\n" + "="*60)
    print("📊 按方案類型統計總計")
    print("="*60)
    
    plan_summary = {}
    
    def safe_to_numeric(value):
        """安全地將值轉換為數字"""
        if pd.isna(value) or value == "" or value is None:
            return 0
        if isinstance(value, (int, float)):
            return float(value) if not pd.isna(value) else 0
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ["錯誤", "error", "none", "n/a", "rate_limited", "未知"]:
                return 0
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0
        return 0
    
    for result in all_results:
        plan = result.get("計劃", "未知方案")
        if plan not in plan_summary:
            plan_summary[plan] = {
                "域名數量": 0,
                "總請求數": 0,
                "總流量(MB)": 0,
                "緩存流量(MB)": 0,
                "緩存請求數": 0,
                "DNS查詢數": 0
            }
        
        plan_summary[plan]["域名數量"] += 1
        plan_summary[plan]["總請求數"] += safe_to_numeric(result.get("總請求數", 0))
        plan_summary[plan]["總流量(MB)"] += safe_to_numeric(result.get("總流量(MB)", 0))
        plan_summary[plan]["緩存流量(MB)"] += safe_to_numeric(result.get("緩存流量(MB)", 0))
        plan_summary[plan]["緩存請求數"] += safe_to_numeric(result.get("緩存請求數", 0))
        plan_summary[plan]["DNS查詢數"] += safe_to_numeric(result.get("DNS查詢數", 0))
    
    # 輸出統計結果
    print("\n方案類型統計：")
    print("-" * 100)
    print(f"{'方案類型':<20} {'域名數':<10} {'總請求數':<20} {'總流量(MB)':<20} {'緩存流量(MB)':<20} {'緩存請求數':<20} {'DNS查詢數':<20}")
    print("-" * 100)
    
    total_summary = {
        "域名數量": 0,
        "總請求數": 0,
        "總流量(MB)": 0,
        "緩存流量(MB)": 0,
        "緩存請求數": 0,
        "DNS查詢數": 0
    }
    
    for plan, stats in sorted(plan_summary.items()):
        print(f"{plan:<20} {stats['域名數量']:<10} {stats['總請求數']:>15,.0f} {stats['總流量(MB)']:>15,.2f} {stats['緩存流量(MB)']:>15,.2f} {stats['緩存請求數']:>15,.0f} {stats['DNS查詢數']:>15,.0f}")
        total_summary["域名數量"] += stats["域名數量"]
        total_summary["總請求數"] += stats["總請求數"]
        total_summary["總流量(MB)"] += stats["總流量(MB)"]
        total_summary["緩存流量(MB)"] += stats["緩存流量(MB)"]
        total_summary["緩存請求數"] += stats["緩存請求數"]
        total_summary["DNS查詢數"] += stats["DNS查詢數"]
    
    print("-" * 100)
    print(f"{'總計':<20} {total_summary['域名數量']:<10} {total_summary['總請求數']:>15,.0f} {total_summary['總流量(MB)']:>15,.2f} {total_summary['緩存流量(MB)']:>15,.2f} {total_summary['緩存請求數']:>15,.0f} {total_summary['DNS查詢數']:>15,.0f}")
    print("-" * 100)
    
    # 保存統計結果到 CSV
    summary_rows = []
    for plan, stats in sorted(plan_summary.items()):
        summary_rows.append({
            "方案類型": plan,
            "域名數量": stats["域名數量"],
            "總請求數": f"{stats['總請求數']:,.0f}",
            "總流量(MB)": f"{stats['總流量(MB)']:,.2f}",
            "緩存流量(MB)": f"{stats['緩存流量(MB)']:,.2f}",
            "緩存請求數": f"{stats['緩存請求數']:,.0f}",
            "DNS查詢數": f"{stats['DNS查詢數']:,.0f}"
        })
    
    summary_rows.append({
        "方案類型": "總計",
        "域名數量": total_summary["域名數量"],
        "總請求數": f"{total_summary['總請求數']:,.0f}",
        "總流量(MB)": f"{total_summary['總流量(MB)']:,.2f}",
        "緩存流量(MB)": f"{total_summary['緩存流量(MB)']:,.2f}",
        "緩存請求數": f"{total_summary['緩存請求數']:,.0f}",
        "DNS查詢數": f"{total_summary['DNS查詢數']:,.0f}"
    })
    
    summary_csv = f"mlytics_plan_summary_{timestamp}.csv"
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    print(f"\n💾 方案類型統計結果已保存到: {summary_csv}")
    
    # 保存所有結果的摘要
    print("\n" + "="*60)
    print("✅ 所有帳戶處理完成！")
    print("="*60)
    print(f"📊 共處理了 {len(all_results)} 個域名")
    print(f"📁 結果檔案: {results_csv}")
    print(f"📁 失敗記錄: {failed_domains_csv}")
    print(f"📁 方案統計: {summary_csv}")
    
    # 保存失敗的域名列表
    if failed_domains:
        print(f"\n⚠️  共有 {len(failed_domains)} 個域名處理失敗")
        df_failed = pd.DataFrame(failed_domains)
        df_failed.to_csv(failed_domains_csv, index=False, encoding="utf-8-sig")
        print(f"📁 失敗的域名已保存到 {failed_domains_csv}")
        print("\n失敗的域名列表:")
        try:
            print(df_failed[["帳戶", "域名", "操作", "失敗原因"]])
        except KeyError:
            print(df_failed)
    else:
        print("\n✅ 所有域名處理成功，無失敗記錄")

if __name__ == "__main__":
    main()

