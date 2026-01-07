import requests
import pandas as pd
import datetime
import json
import time
import random
import os
import sys

# 多個帳戶的認證信息列表
accounts = [
    {
        "email": "3rd@remotes.com.tw",
        "api_key": "5587ba7c3f9ca21c0d5f092dcb5db945a3406",
        "account_id": "29669b64c37f5cd23c3a4000b754a6f1"
    },
    {
        "email": "noc@568win.com",
        "api_key": "12b3f0faf4273464c3258af479abceeef0787",
        "account_id": "91657688541c82a4d428a74f51336805"
    },
    {
        "email": "qbq.humble@gmail.com",
        "api_key": "a826104d7f78717a4724b7a62f43cb8b3c534",
        "account_id": "20ee3ac7c8cedd7a68dc36dc4cfcee74"
    },
    {
        "email": "ron.chang@568win.com",
        "api_key": "ec757a877b27eacc0a80a9017113be47b15f6",
        "account_id": "096347c0cde6db392f6cb11c04e05683"
    }
]

# 依 email 快速查找帳戶資訊
account_map = {acc["email"]: acc for acc in accounts}

# 計算日期範圍：過去 7 天
end_date = datetime.datetime.now(datetime.timezone.utc).date()
start_date = end_date - datetime.timedelta(days=7)
# 轉成 UTC 時間戳，供 DNS GraphQL 使用
start_datetime = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=datetime.timezone.utc)
end_datetime = datetime.datetime.combine(end_date, datetime.time.min, tzinfo=datetime.timezone.utc)

# DNS 查詢時間窗口（根據計劃類型動態調整）
# ⚠️ 重要說明：DNS Analytics API 與 HTTP Analytics API 的限制不同
# 
# HTTP Analytics (GraphQL API) - 用於 get_zone_metric()：
#   - Free Plan: 可以查詢過去 7 天的資料
#   - 其他計劃: 可以查詢更長時間
#
# DNS Analytics (REST API) - 用於 get_dns_query_count()：
#   - Free Website: 6 小時（Cloudflare 官方限制）
#   - Pro: 24 小時
#   - Business: 30 天
#   - Enterprise: 30 天
#   - 其他計劃: 30 天（預設）
#
# 這就是為什麼 Free Plan 的域名可以看到 7 天的 HTTP 數據，
# 但 DNS 查詢數據只能看到 6 小時的原因。
def get_dns_time_window(plan_name):
    plan_lower = (plan_name or "").lower()
    
    # 根據計劃類型設定查詢時間範圍
    if "free" in plan_lower:
        # Free 計劃：只能查詢 6 小時（官方限制）
        window_hours = 6
        dns_end = datetime.datetime.now(datetime.timezone.utc)
        dns_start = dns_end - datetime.timedelta(hours=window_hours)
        time_range_desc = "6H"
        print(f"  📊 使用 Free 計劃限制：查詢最近 6 小時的數據")
    elif "pro" in plan_lower:
        # Pro 計劃：查詢 24 小時
        window_hours = 24
        dns_end = datetime.datetime.now(datetime.timezone.utc)
        dns_start = dns_end - datetime.timedelta(hours=window_hours)
        time_range_desc = "24H"
        print(f"  📊 使用 Pro 計劃限制：查詢最近 24 小時的數據")
    elif "business" in plan_lower:
        # Business 計劃：可以查詢 30 天
        window_days = 30
        dns_end = end_datetime
        dns_start = max(start_datetime, dns_end - datetime.timedelta(days=window_days))
        time_range_desc = "30D"
        print(f"  📊 使用 Business 計劃限制：查詢最近 {window_days} 天的數據")
    elif "enterprise" in plan_lower:
        # Enterprise 計劃：查詢 30 天
        window_days = 30
        dns_end = end_datetime
        dns_start = max(start_datetime, dns_end - datetime.timedelta(days=window_days))
        time_range_desc = "30D"
        print(f"  📊 使用 Enterprise 計劃限制：查詢最近 {window_days} 天的數據")
    else:
        # 未知計劃：預設使用 30 天
        window_days = 30
        dns_end = end_datetime
        dns_start = max(start_datetime, dns_end - datetime.timedelta(days=window_days))
        time_range_desc = "30D"
        print(f"  📊 未知計劃類型，使用預設限制：查詢最近 {window_days} 天的數據")
    
    # REST API 需要 YYYY-MM-DDTHH:MM:SSZ 格式
    # 確保格式正確：將 datetime 轉換為 ISO 格式並替換時區標記
    dns_start_str = dns_start.isoformat().replace("+00:00", "Z")
    dns_end_str = dns_end.isoformat().replace("+00:00", "Z")
    return (dns_start_str, dns_end_str, time_range_desc)

print("="*60)
print("🚀 Cloudflare 數據收集腳本啟動")
print("="*60)
print(f"📅 查詢日期範圍：{start_date} 至 {end_date}")
print(f"📋 帳戶數量：{len(accounts)}")
print("="*60)

# 記錄因速率限制而失敗的請求，稍後重試
rate_limited_requests = []

# 記錄所有失敗的域名及原因
failed_domains = []

# 記錄需要重試的失敗域名（包含完整信息）
failed_zones_to_retry = []

# 自定義異常：用於跳過不支援的域名（如計劃不支援 DNS Analytics）
class SkipZone(Exception):
    """非致命錯誤，用於跳過不支援的域名"""
    pass

# 重試函數 - 處理速率限制
def retry_with_backoff(func, *args, max_retries=3, initial_backoff=10, domain_info=None, **kwargs):
    retries = 0
    while retries < max_retries:
        try:
            result = func(*args, **kwargs)
            return result, True  # 成功，返回結果和成功標誌
        except Exception as e:
            error_message = str(e).lower()
            # 檢查是否為速率限制錯誤
            if "rate limiter budget depleted" in error_message or "rate limit" in error_message:
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
    
    # 如果所有重試都失敗，返回None和成功標誌
    return None, True

# 獲取所有域名列表 - 修改為接受帳戶認證信息
def get_all_zones(account, limit=None):
    email = account["email"]
    api_key = account["api_key"]
    account_id = account["account_id"]
    
    print(f"正在獲取帳戶 {email} 的所有域名列表...")
    
    # 設定 API 請求頭 - 使用 Global API Key 認證
    headers = {
        "X-Auth-Email": email,
        "X-Auth-Key": api_key,
        "Content-Type": "application/json"
    }
    
    zones = []
    page = 1
    per_page = 50
    
    while True:
        try:
            url = f"https://api.cloudflare.com/client/v4/zones?page={page}&per_page={per_page}&account.id={account_id}"
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if not data.get("success", False):
                print(f"獲取域名列表失敗: {data.get('errors', '未知錯誤')}")
                return []
            
            results = data.get("result", [])
            
            # 為每個結果添加帳戶信息
            for zone in results:
                zone["account_email"] = email
                zone["account_id"] = account_id
            
            zones.extend(results)
            
            if limit and len(zones) >= limit:
                zones = zones[:limit]
                break
            
            if len(results) < per_page:
                break
                
            page += 1
            # 添加輕微延遲，避免觸發速率限制
            time.sleep(0.5)
            
        except Exception as e:
            print(f"獲取域名列表時出錯: {str(e)}")
            time.sleep(2)  # 出錯後等待一下再重試
            continue
    
    print(f"帳戶 {email} 找到 {len(zones)} 個域名")
    return zones

# 獲取每個域名的計劃類型 - 修改為接受帳戶信息
def get_zone_plan(zone_id, zone_name, account):
    email = account["email"]
    api_key = account["api_key"]
    
    # 設定 API 請求頭
    headers = {
        "X-Auth-Email": email,
        "X-Auth-Key": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"正在獲取帳戶 {email} 的域名 {zone_name} 的計劃信息...")
    
    domain_info = {
        "帳戶": email,
        "域名": zone_name,
        "zone_id": zone_id,
        "操作": "獲取計劃類型",
        "失敗時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    def _get_zone_plan():
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"HTTP 狀態碼: {response.status_code}")
            
        data = response.json()
        
        if not data.get("success", False):
            raise Exception(f"API 響應錯誤: {data.get('errors', '未知錯誤')}")
        
        plan = "未知計劃"
        if "result" in data and data["result"]:
            plan_info = data["result"].get("plan", {})
            if plan_info:
                plan_name = plan_info.get("name", "")
                if plan_name:
                    return plan_name
        
        return plan
    
    # 使用重試機制獲取計劃
    result, _ = retry_with_backoff(_get_zone_plan, max_retries=3, initial_backoff=5, domain_info=domain_info)
    
    if result is None:
        # 如果獲取失敗，返回默認值
        return "未知計劃"
    
    return result

# 使用 GraphQL 查詢獲取單個指標 - 修改為接受帳戶信息
# 注意：這個 API (HTTP Analytics) 對 Free Plan 可以查詢過去 7 天的資料
# 與 DNS Analytics API 不同，DNS Analytics API 對 Free Plan 只能查詢 6 小時
def get_zone_metric(zone_id, zone_name, metric_name, account):
    email = account["email"]
    api_key = account["api_key"]
    
    # 設定 API 請求頭
    headers = {
        "X-Auth-Email": email,
        "X-Auth-Key": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"正在獲取帳戶 {email} 的域名 {zone_name} 的 {metric_name} 指標...")
    
    domain_info = {
        "帳戶": email,
        "域名": zone_name,
        "zone_id": zone_id,
        "操作": f"獲取{metric_name}指標",
        "失敗時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    def _get_zone_metric():
        # GraphQL 查詢語句
        query = f"""
        query {{
          viewer {{
            zones(filter: {{zoneTag: "{zone_id}"}}) {{
              httpRequests1dGroups(limit: 7, filter: {{date_geq: "{start_date}", date_lt: "{end_date}"}}) {{
                dimensions {{
                  date
                }}
                sum {{
                  {metric_name}
                }}
              }}
            }}
          }}
        }}
        """
        
        # 發送查詢請求
        response = requests.post(
            "https://api.cloudflare.com/client/v4/graphql",
            headers=headers,
            data=json.dumps({"query": query})
        )
        
        # 檢查 HTTP 回應狀態
        if response.status_code != 200:
            # 嘗試解析錯誤訊息
            try:
                error_data = response.json()
                errors = error_data.get("errors", [])
                if errors:
                    error_messages = []
                    for err in errors:
                        error_code = err.get("code", "N/A")
                        error_msg = err.get("message", "未知錯誤")
                        error_messages.append(f"Code: {error_code}, Message: {error_msg}")
                    full_error = " | ".join(error_messages)
                else:
                    full_error = f"HTTP {response.status_code}: {response.text[:200]}"
            except:
                full_error = f"HTTP {response.status_code}: {response.text[:200]}"
            raise Exception(f"HTTP {response.status_code} - {full_error}")
        
        data = response.json()
        
        # 檢查 GraphQL 錯誤
        if "errors" in data and data["errors"]:
            # 收集所有 GraphQL 錯誤訊息
            error_messages = []
            for err in data["errors"]:
                error_code = err.get("code", "N/A")
                error_msg = err.get("message", "未知錯誤")
                error_path = err.get("path", [])
                error_messages.append(f"Code: {error_code}, Message: {error_msg}, Path: {error_path}")
            full_error = " | ".join(error_messages)
            raise Exception(f"GraphQL 錯誤 - {full_error}")
        
        # 安全地遍歷 JSON 結構
        if "data" not in data or data["data"] is None:
            raise Exception("回應中沒有 data 字段")
            
        if "viewer" not in data["data"] or data["data"]["viewer"] is None:
            raise Exception("回應中沒有 viewer 字段")
            
        if "zones" not in data["data"]["viewer"] or not data["data"]["viewer"]["zones"]:
            raise Exception("回應中沒有 zones 字段或為空")
            
        if len(data["data"]["viewer"]["zones"]) == 0:
            raise Exception("zones 列表為空")
            
        if "httpRequests1dGroups" not in data["data"]["viewer"]["zones"][0] or not data["data"]["viewer"]["zones"][0]["httpRequests1dGroups"]:
            raise Exception("回應中沒有 httpRequests1dGroups 字段或為空")
        
        # 安全地獲取記錄
        records = data["data"]["viewer"]["zones"][0]["httpRequests1dGroups"]
        total_value = 0
        
        for entry in records:
            if "sum" in entry and metric_name in entry["sum"]:
                value = entry["sum"][metric_name]
                total_value += value
            
        # 處理度量單位轉換
        if metric_name == "bytes" or metric_name == "cachedBytes":
            # 轉換為 MB
            return round(total_value / (1024 * 1024), 2) if total_value > 0 else 0
        else:
            return total_value if total_value > 0 else 0
    
    # 使用重試機制獲取指標
    result, need_later_retry = retry_with_backoff(_get_zone_metric, max_retries=2, initial_backoff=2, domain_info=domain_info)
    
    if result is None:
        if not need_later_retry:
            # 一般錯誤，返回 "none"
            return "none"
        else:
            # 速率限制錯誤，記錄並返回特殊標記
            rate_limited_requests.append({
                "zone_id": zone_id,
                "zone_name": zone_name,
                "metric_name": metric_name,
                "account": account  # 包含帳戶信息
            })
            return "rate_limited"
    
    return result

# 獲取單個域名的 DNS 查詢總數（包含所有子域名）
# 會嘗試較長的時間範圍，如果失敗則回退到較短的時間範圍
# 並在結果中標注實際使用的時間範圍
def get_dns_query_count(zone_id, zone_name, account, plan_name=None):
    email = account["email"]
    api_key = account["api_key"]
    account_id = account["account_id"]
    
    plan_lower = (plan_name or "").lower()
    
    headers = {
        "X-Auth-Email": email,
        "X-Auth-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # 定義日期區間：優先使用 GraphQL API（使用具體日期區間而不是時間長度）
    end_date = datetime.datetime.now(datetime.timezone.utc).date()
    
    if "free" in plan_lower:
        # Free Plan: GraphQL 可以查最多 7 天（604800 秒），使用具體日期區間
        # 例如：12/10-12/16（7 天，從 12/10 開始到 12/16 結束）
        graphql_start_date = end_date - datetime.timedelta(days=6)  # 往前推 6 天，共 7 天（包含今天）
        graphql_end_date = end_date
        graphql_start_date_str = graphql_start_date.strftime("%Y-%m-%d")
        graphql_end_date_str = graphql_end_date.strftime("%Y-%m-%d")
        time_range_desc = f"{graphql_start_date_str}~{graphql_end_date_str}"
        csv_time_range = "7天"  # CSV 中顯示查詢天數
        rest_hours = 6
    elif "pro" in plan_lower:
        # Pro Plan: GraphQL 可以查 30 天，使用具體日期區間
        graphql_start_date = end_date - datetime.timedelta(days=29)  # 往前推 29 天，共 30 天（包含今天）
        graphql_end_date = end_date
        graphql_start_date_str = graphql_start_date.strftime("%Y-%m-%d")
        graphql_end_date_str = graphql_end_date.strftime("%Y-%m-%d")
        time_range_desc = f"{graphql_start_date_str}~{graphql_end_date_str}"
        csv_time_range = "30天"  # CSV 中顯示查詢天數
        rest_hours = 24
    else:
        # Business/Enterprise: 都可以查 30 天
        graphql_start_date = end_date - datetime.timedelta(days=29)  # 往前推 29 天，共 30 天（包含今天）
        graphql_end_date = end_date
        graphql_start_date_str = graphql_start_date.strftime("%Y-%m-%d")
        graphql_end_date_str = graphql_end_date.strftime("%Y-%m-%d")
        time_range_desc = f"{graphql_start_date_str}~{graphql_end_date_str}"
        csv_time_range = "30天"  # CSV 中顯示查詢天數
        rest_hours = 24 * 30  # 30 天換算為小時
    
    # GraphQL API 查詢函數（使用日期區間而不是時間長度）
    def _get_dns_queries_graphql(start_date_str, end_date_str):
        # 使用具體的日期區間（例如：2025-12-10 到 2025-12-16）
        # start_date_str 和 end_date_str 已經是 YYYY-MM-DD 格式的字符串
        
        # 首先嘗試使用 introspection 查詢查看可用字段（僅在第一次失敗時使用）
        # 然後嘗試不同的查詢結構
        # 方法1：嘗試使用 count 字段（GraphQL 常見的計數字段）
        # 查詢所有 DNS 查詢（使用 date 作為唯一維度，會自動聚合所有查詢類型）
        # 根據實際 API 響應，返回的字段是 count（不是 sum.queryCount）
        query = f"""
        query {{
          viewer {{
            zones(filter: {{zoneTag: "{zone_id}"}}) {{
              dnsAnalyticsAdaptiveGroups(
                limit: 1000
                filter: {{
                  date_geq: "{start_date_str}"
                  date_leq: "{end_date_str}"
                }}
                orderBy: [date_DESC]
              ) {{
                dimensions {{
                  date
                }}
                count
              }}
            }}
          }}
        }}
        """
        
        print(f"  🔍 嘗試 GraphQL 查詢（使用 count 字段，聚合所有查詢類型）...")
        
        response = requests.post(
            "https://api.cloudflare.com/client/v4/graphql",
            headers=headers,
            data=json.dumps({"query": query}),
            timeout=60
        )
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                errors = error_data.get("errors", [])
                if errors:
                    error_messages = []
                    for err in errors:
                        error_code = err.get("code", "N/A")
                        error_msg = err.get("message", "未知錯誤")
                        error_messages.append(f"Code: {error_code}, Message: {error_msg}")
                    full_error = " | ".join(error_messages)
                else:
                    full_error = f"HTTP {response.status_code}: {response.text[:200]}"
            except:
                full_error = f"HTTP {response.status_code}: {response.text[:200]}"
            raise Exception(f"GraphQL DNS Analytics HTTP {response.status_code} - {full_error}")
        
        data = response.json()
        
        if "errors" in data and data["errors"]:
            error_messages = []
            adjusted_successfully = False
            for err in data["errors"]:
                error_code = err.get("code", "N/A")
                error_msg = err.get("message", "未知錯誤")
                error_path = err.get("path", [])
                error_locations = err.get("locations", [])
                error_messages.append(f"Code: {error_code}, Message: {error_msg}, Path: {error_path}, Locations: {error_locations}")
            full_error = " | ".join(error_messages)
            # 記錄完整錯誤以便調試
            print(f"  🔍 GraphQL API 錯誤詳情: {full_error}")
            
            # 如果時間範圍太大，嘗試調整為較小的範圍
            if "time range is too large" in full_error.lower() or "can't be wider than" in full_error.lower():
                # 提取限制值（例如：604800s）
                import re
                match = re.search(r"can't be wider than (\d+)s", full_error)
                if match:
                    max_seconds = int(match.group(1))
                    max_days = max_seconds / (24 * 3600)
                    print(f"  🔍 GraphQL API 時間範圍限制：{max_seconds} 秒（約 {max_days:.2f} 天）")
                    # 調整為略小於限制（減去 2 小時的緩衝，確保不超過）
                    adjusted_seconds = max_seconds - 2 * 3600  # 減去 2 小時的緩衝
                    adjusted_days = adjusted_seconds / (24 * 3600)
                    print(f"  🔍 調整時間範圍為 {adjusted_days:.2f} 天（{adjusted_seconds} 秒）以符合限制")
                    # 重新計算日期範圍
                    adjusted_end_time = datetime.datetime.now(datetime.timezone.utc)
                    adjusted_start_time = adjusted_end_time - datetime.timedelta(seconds=adjusted_seconds)
                    adjusted_start_date_str = adjusted_start_time.date().strftime("%Y-%m-%d")
                    adjusted_end_date_str = adjusted_end_time.date().strftime("%Y-%m-%d")
                    
                    # 重新構建查詢
                    adjusted_query = f"""
                    query {{
                      viewer {{
                        zones(filter: {{zoneTag: "{zone_id}"}}) {{
                          dnsAnalyticsAdaptiveGroups(
                            limit: 1000
                            filter: {{
                              date_geq: "{adjusted_start_date_str}"
                              date_leq: "{adjusted_end_date_str}"
                            }}
                            orderBy: [date_DESC]
                          ) {{
                            dimensions {{
                              date
                            }}
                            count
                          }}
                        }}
                      }}
                    }}
                    """
                    
                    adjusted_response = requests.post(
                        "https://api.cloudflare.com/client/v4/graphql",
                        headers=headers,
                        data=json.dumps({"query": adjusted_query}),
                        timeout=60
                    )
                    
                    if adjusted_response.status_code == 200:
                        adjusted_data = adjusted_response.json()
                        if "errors" not in adjusted_data or not adjusted_data["errors"]:
                            # 使用調整後的響應繼續處理，跳過錯誤處理邏輯
                            print(f"  ✓ 時間範圍調整成功，繼續處理數據...")
                            data = adjusted_data
                            adjusted_successfully = True
                        else:
                            # 調整後仍然失敗，拋出異常
                            raise Exception(f"調整時間範圍後仍然失敗: {adjusted_data.get('errors', [])}")
                    else:
                        raise Exception(f"調整時間範圍後 HTTP 請求失敗: {adjusted_response.status_code}")
            
            # 如果成功調整了時間範圍，跳過錯誤拋出，直接繼續處理
            if not adjusted_successfully:
                # 如果 count 字段也失敗，嘗試使用 introspection 查詢查看可用字段
                if "unknown field" in full_error.lower() and ("count" in full_error.lower() or "sum" in full_error.lower()):
                    print(f"  🔍 嘗試使用 GraphQL Introspection 查詢查看可用字段...")
                    introspection_query = """
                    query IntrospectionQuery {
                      __type(name: "DnsAnalyticsAdaptiveGroups") {
                        name
                        fields {
                          name
                          type {
                            name
                            kind
                          }
                        }
                      }
                    }
                    """
                    try:
                        introspection_response = requests.post(
                            "https://api.cloudflare.com/client/v4/graphql",
                            headers=headers,
                            data=json.dumps({"query": introspection_query}),
                            timeout=60
                        )
                        if introspection_response.status_code == 200:
                            introspection_data = introspection_response.json()
                            print(f"  🔍 Introspection 響應: {json.dumps(introspection_data, indent=2)[:2000]}")
                    except Exception as e:
                        print(f"  🔍 Introspection 查詢失敗: {str(e)}")
                
                # 如果有 data 字段，也輸出它（可能包含部分數據）
                if "data" in data and data["data"]:
                    print(f"  🔍 GraphQL API 部分數據: {json.dumps(data['data'], indent=2)[:1000]}")
                
                raise Exception(f"GraphQL DNS Analytics 錯誤 - {full_error}")
        
        # 解析 GraphQL 回應
        if "data" not in data or data["data"] is None:
            print(f"  🔍 GraphQL API 完整響應（無 data）: {json.dumps(data, indent=2)[:2000]}")
            raise Exception("GraphQL 回應中沒有 data 字段")
        
        if "viewer" not in data["data"] or data["data"]["viewer"] is None:
            print(f"  🔍 GraphQL API 數據結構: {json.dumps(data['data'], indent=2)[:1000]}")
            raise Exception("GraphQL 回應中沒有 viewer 字段")
        
        zones = data["data"]["viewer"].get("zones", [])
        if not zones or len(zones) == 0:
            raise Exception("GraphQL 回應中沒有 zones 或為空")
        
        dns_groups = zones[0].get("dnsAnalyticsAdaptiveGroups", [])
        if not dns_groups:
            # 如果沒有數據，檢查是否有其他字段
            print(f"  ⚠️  GraphQL API 返回空數據，zone 的所有字段: {list(zones[0].keys())}")
            return 0
        
        # 累加所有日期的查詢數
        # 根據實際 API 響應，數據結構為：{"count": 210, "dimensions": {"date": "2025-12-16"}}
        total_queries = 0
        for group in dns_groups:
            # 方法1：使用 count 字段（GraphQL dnsAnalyticsAdaptiveGroups 返回的字段）
            if "count" in group:
                count = group.get("count")
                # 注意：count 可能是 0，應該包含在總和中
                if count is not None:
                    total_queries += int(count)
                    continue  # 如果找到 count，就不需要檢查其他字段了
            # 方法2：使用 sum.queryCount（與 HTTP Analytics 一致，備用）
            if "sum" in group and isinstance(group["sum"], dict) and "queryCount" in group["sum"]:
                query_count = group["sum"]["queryCount"]
                if query_count is not None:
                    total_queries += int(query_count)
                    continue
            # 方法3：直接使用 queryCount 字段（備用）
            if "queryCount" in group:
                query_count = group["queryCount"]
                if query_count is not None:
                    total_queries += int(query_count)
                    continue
            # 方法4：使用 metrics 字段（備用）
            if "metrics" in group and isinstance(group["metrics"], dict) and "queryCount" in group["metrics"]:
                query_count = group["metrics"]["queryCount"]
                if query_count is not None:
                    total_queries += int(query_count)
        
        # 調試：顯示每日查詢數以便驗證
        if len(dns_groups) > 0:
            daily_counts = []
            daily_sum = 0
            for group in dns_groups:
                # 優先使用 count 字段
                if "count" in group:
                    date = group.get("dimensions", {}).get("date", "未知日期")
                    count = group.get("count", 0)
                    if count is not None:
                        count_int = int(count)
                        daily_counts.append(f"{date}: {count_int:,}")
                        daily_sum += count_int
                # 備用：使用 sum.queryCount
                elif "sum" in group and isinstance(group["sum"], dict) and "queryCount" in group["sum"]:
                    date = group.get("dimensions", {}).get("date", "未知日期")
                    count = group["sum"]["queryCount"]
                    if count is not None:
                        count_int = int(count)
                        daily_counts.append(f"{date}: {count_int:,}")
                        daily_sum += count_int
            
            # 驗證加總是否正確
            if daily_sum != total_queries:
                print(f"  ⚠️  警告：每日加總 ({daily_sum:,}) 與總計 ({total_queries:,}) 不一致")
            
            # 只顯示前7個日期的詳細信息
            daily_info = ', '.join(daily_counts[:7])
            if len(daily_counts) > 7:
                daily_info += f', ... (共{len(daily_counts)}天)'
            print(f"  ✓ DNS 查詢總數: {total_queries:,} [每日: {daily_info}]")
        else:
            print(f"  ✓ DNS 查詢總數: {total_queries:,}")
        
        return total_queries
    
    # REST API 查詢函數（備用方案）
    def _get_dns_queries_rest(since_iso, until_iso, csv_range):
        # REST API 需要 YYYY-MM-DDTHH:MM:SSZ 格式
        # 確保日期格式正確（例如：2025-12-07T00:00:00Z）
        since = since_iso  # 格式：YYYY-MM-DDTHH:MM:SSZ
        until = until_iso    # 格式：YYYY-MM-DDTHH:MM:SSZ
        
        # 使用 REST API: /zones/{zone_id}/dns_analytics/report
        # 這個 API 會返回整個 zone 的總查詢數（包含所有子域名）
        # 例如：mm777global.com 會包含 www.mm777global.com, _dmarc.mm777global.com 等所有子域名的查詢
        # 注意：如果不指定 dimensions，API 會返回總計（不需要按日期分組）
        params = {
            "metrics": "queryCount",
            # 不指定 dimensions，直接獲取總計
            "since": since,
            "until": until,
        }
        
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_analytics/report",
            headers=headers,
            params=params,
            timeout=60
        )
        
        # 詳細記錄 API 回應（用於除錯）
        if response.status_code != 200:
            try:
                error_data = response.json()
                errors = error_data.get("errors", [])
                if errors:
                    # 收集所有錯誤訊息
                    error_messages = []
                    for err in errors:
                        error_code = err.get("code", "N/A")
                        error_msg = err.get("message", "未知錯誤")
                        error_messages.append(f"Code: {error_code}, Message: {error_msg}")
                    full_error = " | ".join(error_messages)
                else:
                    full_error = f"HTTP {response.status_code}: {response.text[:200]}"
            except:
                full_error = f"HTTP {response.status_code}: {response.text[:200]}"
            
            if response.status_code == 403:
                raise SkipZone(f"DNS Analytics 403 (無權限) - {full_error}")
            if response.status_code == 400:
                # 400 錯誤通常是計劃不支援或參數錯誤
                raise SkipZone(f"DNS Analytics 400 - {full_error}")
            raise Exception(f"HTTP {response.status_code} - {full_error}")
        
        data = response.json()
        if not data.get("success", False):
            errors = data.get("errors", [])
            if errors:
                # 收集所有錯誤訊息
                error_messages = []
                for err in errors:
                    error_code = err.get("code", "N/A")
                    error_msg = err.get("message", "未知錯誤")
                    error_messages.append(f"Code: {error_code}, Message: {error_msg}")
                full_error = " | ".join(error_messages)
            else:
                full_error = "未知錯誤"
            
            # 檢查是否為計劃不支援的錯誤
            error_msg_lower = full_error.lower()
            if "plan not eligible" in error_msg_lower or "not eligible" in error_msg_lower or "dimension" in error_msg_lower:
                raise SkipZone(f"DNS Analytics 不支援 - {full_error}")
            raise Exception(f"API 錯誤 - {full_error}")
        
        try:
            # 解析返回的數據
            result = data.get("result", {})
            
            # 優先使用 totals（最準確的總計）
            if "totals" in result:
                totals = result.get("totals", {})
                query_count = totals.get("queryCount", 0)
                if query_count:
                    return int(query_count)
            
            # 如果沒有 totals，嘗試從 data 陣列累加
            rows = result.get("data", [])
            if not rows:
                return 0
            
            # 處理 data 陣列
            total = 0
            for row in rows:
                metrics = row.get("metrics", None)
                
                # metrics 可能是物件 {"queryCount": 123} 或陣列 [123]
                if isinstance(metrics, dict):
                    # 物件格式：{"queryCount": 123}
                    query_count = metrics.get("queryCount", 0)
                    total += int(query_count) if query_count else 0
                elif isinstance(metrics, list) and len(metrics) > 0:
                    # 陣列格式：[123] - 第一個元素就是查詢數
                    total += int(metrics[0]) if metrics[0] else 0
                else:
                    # 其他格式，嘗試直接獲取
                    query_count = row.get("queryCount", 0)
                    total += int(query_count) if query_count else 0
            
            return total
        except Exception as e:
            # 詳細記錄解析錯誤
            raise Exception(f"無法解析 DNS 查詢數據: {str(e)} | 回應數據: {json.dumps(data, indent=2)[:500]}")
    
    domain_info = {
        "帳戶": email,
        "域名": zone_name,
        "zone_id": zone_id,
        "操作": "獲取DNS查詢數（包含所有子域名）",
        "失敗時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 優先嘗試 GraphQL API（使用具體日期區間）
    try:
        # 使用計算好的日期區間
        api_desc = "GraphQL API"
        print(f"  → 優先嘗試使用 {api_desc} 獲取 DNS 查詢數據（日期區間：{time_range_desc}）...")
        
        def _call_graphql_api():
            return _get_dns_queries_graphql(graphql_start_date_str, graphql_end_date_str)
        
        result, need_later_retry = retry_with_backoff(
            _call_graphql_api,
            max_retries=2,
            initial_backoff=2,
            domain_info=domain_info
        )
        
        if result is not None:
            print(f"  ✓ {api_desc} 成功獲取 DNS 查詢數據（日期區間：{time_range_desc}）")
            return (result, csv_time_range)
        else:
            print(f"  ⚠️  {api_desc} 失敗，嘗試使用 REST API...")
    except Exception as e:
        error_msg = str(e).lower()
        print(f"  ⚠️  GraphQL API 失敗: {str(e)[:100]}...，嘗試使用 REST API")
    
    # 備用方案：使用 REST API
    if "free" in plan_lower:
        rest_days = rest_hours / 24
        time_range_desc = "6H"
        csv_time_range = "6小時"
        api_desc = "REST API (6小時)"
    elif "pro" in plan_lower:
        rest_days = rest_hours / 24
        time_range_desc = "24H"
        csv_time_range = "24小時"
        api_desc = "REST API (24小時)"
    else:
        rest_days = 30
        time_range_desc = "30D"
        csv_time_range = "30天"
        api_desc = "REST API (30天)"
    
    # 計算 REST API 時間範圍
    end_time = datetime.datetime.now(datetime.timezone.utc)
    if rest_days >= 1:
        start_time = end_time - datetime.timedelta(days=rest_days)
    else:
        start_time = end_time - datetime.timedelta(hours=rest_hours)
    
    since_iso = start_time.isoformat().replace("+00:00", "Z")
    until_iso = end_time.isoformat().replace("+00:00", "Z")
    
    print(f"  → 使用 {api_desc} 獲取 DNS 查詢數據（時間範圍：{time_range_desc}）...")
    
    def _call_rest_api():
        return _get_dns_queries_rest(since_iso, until_iso, csv_time_range)
    
    try:
        result, need_later_retry = retry_with_backoff(
            _call_rest_api,
            max_retries=2,
            initial_backoff=2,
            domain_info=domain_info
        )
        
        if result is not None:
            print(f"  ✓ {api_desc} 成功獲取 DNS 查詢數據（日期區間：{time_range_desc}）")
            return (result, csv_time_range)
        else:
            domain_info["失敗原因"] = "REST API 查詢失敗"
            failed_domains.append(domain_info.copy())
            return ("N/A (查詢失敗)", csv_time_range if 'csv_time_range' in locals() else time_range_desc)
    except SkipZone as e:
        skip_msg = str(e)
        print(f"  ⚠️  {api_desc} 失敗: {skip_msg[:100]}...")
        domain_info["失敗原因"] = f"計劃限制 - {skip_msg}"
        failed_domains.append(domain_info.copy())
        return ("N/A (計劃限制)", csv_time_range if 'csv_time_range' in locals() else time_range_desc)
    except Exception as e:
        error_msg = str(e)
        print(f"  ⚠️  {api_desc} 失敗: {error_msg[:100]}...")
        domain_info["失敗原因"] = f"查詢失敗 - {error_msg}"
        failed_domains.append(domain_info.copy())
        return ("N/A (查詢失敗)", time_range_desc)
    
    # 不應該到達這裡，但以防萬一
    domain_info["失敗原因"] = "所有 API 都無法查詢"
    failed_domains.append(domain_info.copy())
    return ("N/A (查詢失敗)", "未知")

# 處理之前因速率限制而失敗的請求 - 修改為處理多帳戶
def process_rate_limited_requests():
    if not rate_limited_requests:
        return {}
    
    print(f"\n開始處理之前因速率限制而失敗的 {len(rate_limited_requests)} 個請求...")
    print("等待 2 分鐘讓 API 速率限制重置...")
    time.sleep(120)  # 等待 2 分鐘
    
    results = {}
    
    for req in rate_limited_requests:
        zone_id = req["zone_id"]
        zone_name = req["zone_name"]
        metric_name = req["metric_name"]
        account = req["account"]
        plan = req.get("plan")
        
        email = account["email"]
        api_key = account["api_key"]
        
        # 設定 API 請求頭
        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json"
        }
        
        key = f"{zone_name}_{metric_name}"
        print(f"重新嘗試獲取帳戶 {email} 的域名 {zone_name} 的 {metric_name} 指標...")
        
        domain_info = {
            "帳戶": email,
            "域名": zone_name,
            "zone_id": zone_id,
            "操作": f"重試獲取{metric_name}指標",
            "失敗時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 使用更長的退避時間重試
        def _retry_metric():
            # HTTP 指標與 DNS 查詢指標使用不同的 API
            if metric_name == "dnsQueries":
                # 使用 REST API 獲取整個 zone 的總查詢數
                dns_start_iso, dns_end_iso, time_range_desc = get_dns_time_window(plan)
                
                # 根據計劃類型計算 CSV 時間範圍描述
                plan_lower = (plan or "").lower()
                if "free" in plan_lower:
                    csv_range = "6小時"
                elif "pro" in plan_lower:
                    csv_range = "24小時"
                else:
                    csv_range = "30天"
                
                params = {
                    "metrics": "queryCount",
                    # 不指定 dimensions，直接獲取總計
                    "since": dns_start_iso,
                    "until": dns_end_iso,
                }
                
                response = requests.get(
                    f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_analytics/report",
                    headers=headers,
                    params=params,
                    timeout=60
                )
                
                # 詳細記錄 API 回應（用於除錯）
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        errors = error_data.get("errors", [])
                        if errors:
                            error_messages = []
                            for err in errors:
                                error_code = err.get("code", "N/A")
                                error_msg = err.get("message", "未知錯誤")
                                error_messages.append(f"Code: {error_code}, Message: {error_msg}")
                            full_error = " | ".join(error_messages)
                        else:
                            full_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    except:
                        full_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    
                    if response.status_code == 403:
                        raise SkipZone(f"DNS Analytics 403 (無權限) - {full_error}")
                    if response.status_code == 400:
                        raise SkipZone(f"DNS Analytics 400 - {full_error}")
                    raise Exception(f"HTTP {response.status_code} - {full_error}")
                
                data = response.json()
                if not data.get("success", False):
                    errors = data.get("errors", [])
                    if errors:
                        error_messages = []
                        for err in errors:
                            error_code = err.get("code", "N/A")
                            error_msg = err.get("message", "未知錯誤")
                            error_messages.append(f"Code: {error_code}, Message: {error_msg}")
                        full_error = " | ".join(error_messages)
                    else:
                        full_error = "未知錯誤"
                    raise Exception(f"API 錯誤 - {full_error}")
                
                result = data.get("result", {})
                
                # 優先使用 totals（最準確的總計）
                if "totals" in result:
                    totals = result.get("totals", {})
                    query_count = totals.get("queryCount", 0)
                    if query_count:
                        return (int(query_count), csv_range)
                
                # 如果沒有 totals，嘗試從 data 陣列累加
                rows = result.get("data", [])
                if not rows:
                    return (0, csv_range)
                
                # 處理 data 陣列
                total = 0
                for row in rows:
                    metrics = row.get("metrics", None)
                    
                    # metrics 可能是物件 {"queryCount": 123} 或陣列 [123]
                    if isinstance(metrics, dict):
                        # 物件格式：{"queryCount": 123}
                        query_count = metrics.get("queryCount", 0)
                        total += int(query_count) if query_count else 0
                    elif isinstance(metrics, list) and len(metrics) > 0:
                        # 陣列格式：[123] - 第一個元素就是查詢數
                        total += int(metrics[0]) if metrics[0] else 0
                    else:
                        # 其他格式，嘗試直接獲取
                        query_count = row.get("queryCount", 0)
                        total += int(query_count) if query_count else 0
                
                return (total, csv_range)
            else:
                retry_query = f"""
                query {{
                  viewer {{
                    zones(filter: {{zoneTag: "{zone_id}"}}) {{
                      httpRequests1dGroups(limit: 7, filter: {{date_geq: "{start_date}", date_lt: "{end_date}"}}) {{
                        dimensions {{
                          date
                        }}
                        sum {{
                          {metric_name}
                        }}
                      }}
                    }}
                  }}
                }}
                """
            
            response = requests.post(
                "https://api.cloudflare.com/client/v4/graphql",
                headers=headers,
                data=json.dumps({"query": retry_query})
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP 狀態碼: {response.status_code}")
            
            data = response.json()
            
            if "errors" in data and data["errors"]:
                error_msg = data["errors"][0].get("message", "未知錯誤")
                raise Exception(f"GraphQL 錯誤: {error_msg}")
            
            try:
                # DNS 查詢已在上面處理，這裡只處理 HTTP 指標
                records = data["data"]["viewer"]["zones"][0]["httpRequests1dGroups"]
                total_value = 0
                
                for entry in records:
                    if "sum" in entry and metric_name in entry["sum"]:
                        value = entry["sum"][metric_name]
                        total_value += value
                
                if metric_name == "bytes" or metric_name == "cachedBytes":
                    return round(total_value / (1024 * 1024), 2) if total_value > 0 else 0
                else:
                    return total_value if total_value > 0 else 0
            except:
                raise Exception("無法從響應中提取數據")
        
        # 使用更長的退避時間
        result, _ = retry_with_backoff(_retry_metric, max_retries=3, initial_backoff=10, domain_info=domain_info)
        
        if result is not None:
            results[key] = result
        else:
            results[key] = "none"
        
        # 添加較長的延遲，避免再次觸發速率限制
        time.sleep(5)
    
    return results

# 從失敗清單 CSV 重新測試失敗的域名（可獨立執行）
def retry_failed_domains_from_csv(failed_csv_path, results_csv, account_map, max_retries=3):
    if not os.path.isfile(failed_csv_path):
        print(f"找不到失敗清單檔案：{failed_csv_path}")
        return [], []
    
    print(f"\n🔄 從 {failed_csv_path} 重新測試失敗的域名（最多重試 {max_retries} 次）")
    df = pd.read_csv(failed_csv_path)
    
    retry_results = []
    failed_again = []
    
    for _, row in df.iterrows():
        email = row.get("帳戶") or row.get("account")
        zone_id = row.get("zone_id") or row.get("zoneId")
        zone_name = row.get("域名") or row.get("domain") or "未知域名"
        status = row.get("狀態", "未知")
        prev_reason = row.get("失敗原因", "未知原因")
        
        if pd.isna(zone_id):
            failed_again.append({
                "帳戶": email,
                "域名": zone_name,
                "狀態": status,
                "計劃": "獲取失敗",
                "失敗原因": f"缺少 zone_id，無法重試（原因: {prev_reason})",
                "總請求數": "錯誤",
                "總流量(MB)": "錯誤",
                "緩存流量(MB)": "錯誤",
                "緩存請求數": "錯誤",
                "DNS查詢數": "錯誤",
                "DNS查詢時間範圍": "錯誤"
            })
            continue
        
        account = account_map.get(email)
        if not account:
            failed_again.append({
                "帳戶": email,
                "域名": zone_name,
                "狀態": status,
                "計劃": "獲取失敗",
                "失敗原因": f"找不到帳戶認證（原因: {prev_reason})",
                "總請求數": "錯誤",
                "總流量(MB)": "錯誤",
                "緩存流量(MB)": "錯誤",
                "緩存請求數": "錯誤",
                "DNS查詢數": "錯誤",
                "DNS查詢時間範圍": "錯誤",
                "zone_id": zone_id
            })
            continue
        
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            retry_count += 1
            print(f"\n  🔄 重新測試域名 [{retry_count}/{max_retries}]: {zone_name} (帳戶: {email})")
            try:
                plan = get_zone_plan(zone_id, zone_name, account)
                time.sleep(1)
                
                bytes_total = get_zone_metric(zone_id, zone_name, "bytes", account)
                time.sleep(1)
                
                requests_count = get_zone_metric(zone_id, zone_name, "requests", account)
                time.sleep(1)
                
                cached_bytes = get_zone_metric(zone_id, zone_name, "cachedBytes", account)
                time.sleep(1)
                
                cached_requests = get_zone_metric(zone_id, zone_name, "cachedRequests", account)
                time.sleep(1)
                
                dns_queries_result = get_dns_query_count(zone_id, zone_name, account, plan)
                if isinstance(dns_queries_result, tuple):
                    dns_queries, dns_time_range = dns_queries_result
                else:
                    dns_queries = dns_queries_result
                    dns_time_range = "未知"
                time.sleep(1)
                
                retry_results.append({
                    "帳戶": email,
                    "域名": zone_name,
                    "狀態": status,
                    "計劃": plan,
                    "總請求數": requests_count,
                    "總流量(MB)": bytes_total,
                    "緩存流量(MB)": cached_bytes,
                    "緩存請求數": cached_requests,
                    "DNS查詢數": dns_queries,
                    "DNS查詢時間範圍": dns_time_range,
                    "失敗原因": f"外部重試成功（第{retry_count}次）",
                    "zone_id": zone_id
                })
                success = True
                print(f"  ✅ {zone_name} 重新測試成功")
            except Exception as e:
                error_msg = str(e)
                print(f"  ❌ {zone_name} 重新測試失敗: {error_msg[:120]}...")
                if retry_count >= max_retries:
                    failed_again.append({
                        "帳戶": email,
                        "域名": zone_name,
                        "狀態": status,
                        "計劃": "獲取失敗",
                        "失敗原因": f"外部重試{max_retries}次失敗: {error_msg}",
                        "總請求數": "錯誤",
                        "總流量(MB)": "錯誤",
                        "緩存流量(MB)": "錯誤",
                        "緩存請求數": "錯誤",
                        "DNS查詢數": "錯誤",
                        "DNS查詢時間範圍": "錯誤",
                        "zone_id": zone_id
                    })
                else:
                    # 等待再重試
                    wait_sec = 5 * retry_count
                    print(f"  ⏳ 等待 {wait_sec} 秒後再嘗試...")
                    time.sleep(wait_sec)
    
    # 保存重試結果
    if retry_results:
        save_results_to_csv(retry_results, results_csv, is_append=True)
        print(f"\n💾 已將外部重試結果追加到 {results_csv}")
    
    return retry_results, failed_again

# 保存結果到CSV文件
def save_results_to_csv(results, filename, is_append=False):
    # 確保結果列表不是空的
    if not results:
        return
        
    # 轉換為DataFrame
    df = pd.DataFrame(results)
    
    # 移除臨時 zone_id 欄位 (如果存在)
    if "zone_id" in df.columns:
        df = df.drop(columns=["zone_id"])
    
    # 嘗試進行排序（按總流量）
    try:
        df["排序值"] = pd.to_numeric(df["總流量(MB)"], errors="coerce").fillna(-1)
        df = df.sort_values(by="排序值", ascending=False)
        df = df.drop(columns=["排序值"])
    except Exception as e:
        print(f"排序時出錯: {str(e)}")
    
    # 檢查文件是否已存在
    file_exists = os.path.isfile(filename)
    
    # 寫入CSV文件
    if is_append and file_exists:
        # 如果是追加模式且文件已存在
        df.to_csv(filename, mode='a', index=False, header=False, encoding="utf-8-sig")
    else:
        # 新建文件或覆蓋現有文件
        df.to_csv(filename, index=False, encoding="utf-8-sig")
    
    print(f"數據已保存到 {filename}")

# 主函數 - 修改為處理多個帳戶
def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CLI 模式：單獨重新測試失敗清單
    if len(sys.argv) >= 3 and sys.argv[1] == "--retry-failed":
        failed_csv_input = sys.argv[2]
        # 可選第三參數指定輸出文件
        results_csv_override = sys.argv[3] if len(sys.argv) >= 4 else f"cloudflare_retry_{timestamp}.csv"
        retry_results, failed_again = retry_failed_domains_from_csv(failed_csv_input, results_csv_override, account_map)
        
        print("\n" + "="*60)
        print("✅ 重新測試流程完成")
        print("="*60)
        print(f"📁 重試結果已追加到: {results_csv_override}")
        print(f"📊 重試成功: {len([r for r in retry_results if r.get('失敗原因','').startswith('外部重試成功')])}")
        print(f"⚠️ 重試仍失敗: {len(failed_again)}")
        
        # 若仍有失敗，輸出到新檔案
        if failed_again:
            failed_again_csv = f"cloudflare_failed_retry_{timestamp}.csv"
            pd.DataFrame(failed_again).to_csv(failed_again_csv, index=False, encoding="utf-8-sig")
            print(f"📁 仍失敗的域名已保存到 {failed_again_csv}")
        return
    
    # 定義輸出文件名（正常流程）
    results_csv = f"cloudflare_metrics_{timestamp}.csv"
    failed_domains_csv = f"cloudflare_failed_domains_{timestamp}.csv"
    
    print("\n開始獲取多個 Cloudflare 帳戶的域名資訊...")
    
    all_results = []
    total_accounts = len(accounts)
    
    # 為每個帳戶獲取域名信息
    for account_idx, account in enumerate(accounts, 1):
        print(f"\n{'='*60}")
        print(f"📧 處理帳戶 [{account_idx}/{total_accounts}]: {account['email']}")
        print(f"{'='*60}")
        
        # 獲取該帳戶的所有域名
        zones = get_all_zones(account)
        if not zones:
            print(f"帳戶 {account['email']} 沒有找到域名，或者獲取失敗")
            continue
        
        # 每批次處理10個域名，每處理10筆就寫入一次
        batch_size = 10
        processed_count = 0
        
        for i in range(0, len(zones), batch_size):
            batch = zones[i:i+batch_size]
            print(f"\n{'='*60}")
            print(f"處理帳戶 {account['email']} 的第 {i+1} 到 {min(i+batch_size, len(zones))} 個域名 (共 {len(zones)} 個)")
            print(f"{'='*60}")
            
            batch_results = []
            
            for idx, zone in enumerate(batch, 1):
                zone_id = zone["id"]
                zone_name = zone["name"]
                global_idx = i + idx
                
                print(f"\n[{global_idx}/{len(zones)}] 處理域名: {zone_name}")
                
                try:
                    # 獲取計劃類型
                    print(f"  → 獲取計劃類型...")
                    plan = get_zone_plan(zone_id, zone_name, account)
                    print(f"  → 計劃: {plan}")
                    time.sleep(1)
                    
                    # 分別獲取每個指標，並增加延遲
                    print(f"  → 獲取總流量...")
                    bytes_total = get_zone_metric(zone_id, zone_name, "bytes", account)
                    time.sleep(1)
                    
                    print(f"  → 獲取總請求數...")
                    requests_count = get_zone_metric(zone_id, zone_name, "requests", account)
                    time.sleep(1)
                    
                    print(f"  → 獲取緩存流量...")
                    cached_bytes = get_zone_metric(zone_id, zone_name, "cachedBytes", account)
                    time.sleep(1)
                    
                    print(f"  → 獲取緩存請求數...")
                    cached_requests = get_zone_metric(zone_id, zone_name, "cachedRequests", account)
                    time.sleep(1)

                    print(f"  → 獲取DNS查詢數（包含所有子域名）...")
                    dns_queries_result = get_dns_query_count(zone_id, zone_name, account, plan)
                    if isinstance(dns_queries_result, tuple):
                        dns_queries, dns_time_range = dns_queries_result
                    else:
                        # 兼容舊版本（如果返回的不是元組）
                        dns_queries = dns_queries_result
                        dns_time_range = "未知"
                    time.sleep(1)
                    
                    batch_results.append({
                        "帳戶": account["email"],
                        "域名": zone_name,
                        "狀態": zone.get("status", "未知"),
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
                    # 記錄失敗的域名，稍後重試
                    failed_zones_to_retry.append({
                        "zone": zone,
                        "zone_id": zone_id,
                        "zone_name": zone_name,
                        "account": account,
                        "error": error_msg,
                        "retry_count": 0
                    })
                    # 即使失敗也記錄基本信息
                    batch_results.append({
                        "帳戶": account["email"],
                        "域名": zone_name,
                        "狀態": zone.get("status", "未知"),
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
            
            # 處理當前批次因速率限制而失敗的請求
            if rate_limited_requests:
                print(f"\n⚠️  批次中有 {len(rate_limited_requests)} 個請求因速率限制而失敗，等待處理...")
                retry_results = process_rate_limited_requests()
                
                # 更新結果
                for result in batch_results:
                    zone_name = result["域名"]
                    has_rate_limit_issue = False
                    
                    # 檢查並更新每個指標
                    if result["總請求數"] == "rate_limited":
                        key = f"{zone_name}_requests"
                        if key in retry_results:
                            result["總請求數"] = retry_results[key]
                            has_rate_limit_issue = True
                    
                    if result["總流量(MB)"] == "rate_limited":
                        key = f"{zone_name}_bytes"
                        if key in retry_results:
                            result["總流量(MB)"] = retry_results[key]
                            has_rate_limit_issue = True
                    
                    if result["緩存流量(MB)"] == "rate_limited":
                        key = f"{zone_name}_cachedBytes"
                        if key in retry_results:
                            result["緩存流量(MB)"] = retry_results[key]
                            has_rate_limit_issue = True
                    
                    if result["緩存請求數"] == "rate_limited":
                        key = f"{zone_name}_cachedRequests"
                        if key in retry_results:
                            result["緩存請求數"] = retry_results[key]
                            has_rate_limit_issue = True
                    
                    if result.get("DNS查詢數") == "rate_limited":
                        key = f"{zone_name}_dnsQueries"
                        if key in retry_results:
                            retry_value = retry_results[key]
                            if isinstance(retry_value, tuple):
                                result["DNS查詢數"] = retry_value[0]
                                result["DNS查詢時間範圍"] = retry_value[1]
                            else:
                                result["DNS查詢數"] = retry_value
                            has_rate_limit_issue = True
                    
                    # 更新失敗原因
                    if has_rate_limit_issue:
                        if "失敗原因" not in result:
                            result["失敗原因"] = ""
                        elif result.get("失敗原因", "") == "":
                            result["失敗原因"] = "速率限制重試成功"
                        elif "速率限制" in result.get("失敗原因", ""):
                            result["失敗原因"] = result["失敗原因"].replace("速率限制", "速率限制重試成功")
                
                rate_limited_requests.clear()  # 清空處理過的請求
            
            # 添加批次結果到總結果
            all_results.extend(batch_results)
            
            # 每處理 10 筆就寫入一次（批次寫入）
            if len(all_results) == len(batch_results):  # 如果是第一批結果
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
        if account != accounts[-1]:  # 如果不是最後一個帳戶
            print(f"帳戶 {account['email']} 處理完成，休息60秒後處理下一個帳戶...")
            time.sleep(60)
    
    # 處理失敗的域名重試（最多三次）
    if failed_zones_to_retry:
        print("\n" + "="*60)
        print(f"🔄 開始重試失敗的域名（共 {len(failed_zones_to_retry)} 個）")
        print("="*60)
        
        retry_results = []
        max_retries = 3
        
        for retry_attempt in range(1, max_retries + 1):
            if not failed_zones_to_retry:
                break
            
            print(f"\n重試第 {retry_attempt} 次（最多 {max_retries} 次）...")
            print(f"等待 {retry_attempt * 10} 秒後開始重試...")
            time.sleep(retry_attempt * 10)  # 每次重試前等待更長時間
            
            current_failed = failed_zones_to_retry.copy()
            failed_zones_to_retry.clear()
            
            for failed_zone_info in current_failed:
                zone = failed_zone_info["zone"]
                zone_id = failed_zone_info["zone_id"]
                zone_name = failed_zone_info["zone_name"]
                account = failed_zone_info["account"]
                previous_error = failed_zone_info["error"]
                retry_count = failed_zone_info["retry_count"] + 1
                
                print(f"\n  🔄 重試域名 [{retry_count}/{max_retries}]: {zone_name}")
                print(f"     上次錯誤: {previous_error[:100]}...")
                
                try:
                    # 獲取計劃類型
                    plan = get_zone_plan(zone_id, zone_name, account)
                    time.sleep(1)
                    
                    # 分別獲取每個指標
                    bytes_total = get_zone_metric(zone_id, zone_name, "bytes", account)
                    time.sleep(1)
                    
                    requests_count = get_zone_metric(zone_id, zone_name, "requests", account)
                    time.sleep(1)
                    
                    cached_bytes = get_zone_metric(zone_id, zone_name, "cachedBytes", account)
                    time.sleep(1)
                    
                    cached_requests = get_zone_metric(zone_id, zone_name, "cachedRequests", account)
                    time.sleep(1)
                    
                    dns_queries_result = get_dns_query_count(zone_id, zone_name, account, plan)
                    if isinstance(dns_queries_result, tuple):
                        dns_queries, dns_time_range = dns_queries_result
                    else:
                        dns_queries = dns_queries_result
                        dns_time_range = "未知"
                    time.sleep(1)
                    
                    # 重試成功，添加到結果
                    retry_results.append({
                        "帳戶": account["email"],
                        "域名": zone_name,
                        "狀態": zone.get("status", "未知"),
                        "計劃": plan,
                        "總請求數": requests_count,
                        "總流量(MB)": bytes_total,
                        "緩存流量(MB)": cached_bytes,
                        "緩存請求數": cached_requests,
                        "DNS查詢數": dns_queries,
                        "DNS查詢時間範圍": dns_time_range,
                        "失敗原因": f"重試成功（第{retry_count}次）",
                        "zone_id": zone_id
                    })
                    
                    print(f"  ✅ 域名 {zone_name} 重試成功！")
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"  ❌ 域名 {zone_name} 重試失敗: {error_msg[:100]}...")
                    
                    if retry_count < max_retries:
                        # 還未達到最大重試次數，繼續重試
                        failed_zones_to_retry.append({
                            "zone": zone,
                            "zone_id": zone_id,
                            "zone_name": zone_name,
                            "account": account,
                            "error": error_msg,
                            "retry_count": retry_count
                        })
                    else:
                        # 達到最大重試次數，記錄為最終失敗
                        retry_results.append({
                            "帳戶": account["email"],
                            "域名": zone_name,
                            "狀態": zone.get("status", "未知"),
                            "計劃": "獲取失敗",
                            "總請求數": "錯誤",
                            "總流量(MB)": "錯誤",
                            "緩存流量(MB)": "錯誤",
                            "緩存請求數": "錯誤",
                            "DNS查詢數": "錯誤",
                            "DNS查詢時間範圍": "錯誤",
                            "失敗原因": f"重試{max_retries}次後仍失敗: {error_msg}",
                            "zone_id": zone_id
                        })
                        
                        # 同時記錄到 failed_domains
                        failed_domains.append({
                            "帳戶": account["email"],
                            "域名": zone_name,
                            "zone_id": zone_id,
                            "操作": "重試失敗",
                            "失敗時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "失敗原因": f"重試{max_retries}次後仍失敗: {error_msg}"
                        })
            
            if failed_zones_to_retry:
                print(f"\n⚠️  仍有 {len(failed_zones_to_retry)} 個域名需要重試")
            else:
                print(f"\n✅ 所有域名重試完成")
        
        # 將重試結果添加到總結果中
        if retry_results:
            all_results.extend(retry_results)
            print(f"\n📊 重試成功 {len([r for r in retry_results if r.get('失敗原因', '').startswith('重試成功')])} 個域名")
            print(f"📊 重試後仍失敗 {len([r for r in retry_results if not r.get('失敗原因', '').startswith('重試成功')])} 個域名")
            
            # 保存重試結果
            save_results_to_csv(retry_results, results_csv, is_append=True)
            print(f"💾 重試結果已追加到 {results_csv}")
    
    # 按 Plan 分組統計總計
    print("\n" + "="*60)
    print("📊 按計劃類型統計總計")
    print("="*60)
    
    plan_summary = {}
    
    def safe_to_numeric(value):
        """安全地將值轉換為數字，無法轉換則返回 0"""
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
        plan = result.get("計劃", "未知計劃")
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
    print("\n計劃類型統計：")
    print("-" * 100)
    print(f"{'計劃類型':<20} {'域名數':<10} {'總請求數':<20} {'總流量(MB)':<20} {'緩存流量(MB)':<20} {'緩存請求數':<20} {'DNS查詢數':<20}")
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
            "計劃類型": plan,
            "域名數量": stats["域名數量"],
            "總請求數": f"{stats['總請求數']:,.0f}",
            "總流量(MB)": f"{stats['總流量(MB)']:,.2f}",
            "緩存流量(MB)": f"{stats['緩存流量(MB)']:,.2f}",
            "緩存請求數": f"{stats['緩存請求數']:,.0f}",
            "DNS查詢數": f"{stats['DNS查詢數']:,.0f}"
        })
    
    # 添加總計行
    summary_rows.append({
        "計劃類型": "總計",
        "域名數量": total_summary["域名數量"],
        "總請求數": f"{total_summary['總請求數']:,.0f}",
        "總流量(MB)": f"{total_summary['總流量(MB)']:,.2f}",
        "緩存流量(MB)": f"{total_summary['緩存流量(MB)']:,.2f}",
        "緩存請求數": f"{total_summary['緩存請求數']:,.0f}",
        "DNS查詢數": f"{total_summary['DNS查詢數']:,.0f}"
    })
    
    summary_csv = f"cloudflare_plan_summary_{timestamp}.csv"
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    print(f"\n💾 計劃類型統計結果已保存到: {summary_csv}")
    
    # 保存所有結果的摘要
    print("\n" + "="*60)
    print("✅ 所有帳戶處理完成！")
    print("="*60)
    print(f"📊 共處理了 {len(all_results)} 個域名")
    print(f"📁 結果檔案: {results_csv}")
    print(f"📁 失敗記錄: {failed_domains_csv}")
    print(f"📁 計劃統計: {summary_csv}")
    
    # 將所有域名按流量排序的總結果
    try:
        all_df = pd.DataFrame(all_results)
        if "zone_id" in all_df.columns:
            all_df = all_df.drop(columns=["zone_id"])
        
        # 確保所有結果都有"失敗原因"欄位
        if "失敗原因" not in all_df.columns:
            all_df["失敗原因"] = ""
        else:
            # 將空值填充為空字串
            all_df["失敗原因"] = all_df["失敗原因"].fillna("")
        
        all_df["排序值"] = pd.to_numeric(all_df["總流量(MB)"], errors="coerce").fillna(-1)
        all_df = all_df.sort_values(by="排序值", ascending=False)
        all_df = all_df.drop(columns=["排序值"])
        
        # 保存排序後的總結果
        all_sorted_csv = f"cloudflare_all_sorted_{timestamp}.csv"
        all_df.to_csv(all_sorted_csv, index=False, encoding="utf-8-sig")
        print(f"排序後的所有結果已保存到 {all_sorted_csv}")
        
        # 打印前20個流量最大的域名
        print("\n流量最大的前20個域名:")
        print(all_df.head(20))
    except Exception as e:
        print(f"處理總結果時出錯: {str(e)}")
    
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