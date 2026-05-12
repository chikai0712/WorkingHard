import requests
import pandas as pd
import datetime
import json
import time
import random
import os

# 多個帳戶的認證信息列表（從環境變數載入，避免硬編碼憑證）
# 建議使用 API Token（Bearer），最小權限：Zone:Read + DNS Analytics:Read
# 若仍需相容舊的 Global API Key，可在 JSON 內放 api_key + email（不建議長期使用）
# 環境變數範例：
# export CF_ACCOUNTS_JSON='[
#   {"api_token":"<TOKEN>","account_id":"<ACCOUNT_ID>","email":"optional@example.com"},
#   {"api_key":"<GLOBAL_KEY>","email":"user@example.com","account_id":"<ACCOUNT_ID>"}
# ]'
CF_ACCOUNTS_JSON = os.getenv("CF_ACCOUNTS_JSON", "")
if not CF_ACCOUNTS_JSON:
    print("請先設定環境變數 CF_ACCOUNTS_JSON，例如：")
    print('export CF_ACCOUNTS_JSON=\'[{"api_token":"<TOKEN>","account_id":"<ACCOUNT_ID>","email":"optional@example.com"}]\'')
    raise SystemExit(1)

try:
    accounts = json.loads(CF_ACCOUNTS_JSON)
except Exception as e:
    print(f"解析 CF_ACCOUNTS_JSON 失敗: {e}")
    raise SystemExit(1)

# 計算日期範圍：過去 30 天
end_date = datetime.datetime.utcnow().date()
start_date = end_date - datetime.timedelta(days=30)

print(f"查詢日期範圍：{start_date} 至 {end_date}")

# 記錄因速率限制而失敗的請求，稍後重試
rate_limited_requests = []

# 記錄所有失敗的域名及原因
failed_domains = []

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
    token = account.get("api_token")
    api_key = account.get("api_key")
    email = account.get("email", "unknown")
    account_id = account.get("account_id")
    
    print(f"正在獲取帳戶 {email} 的所有域名列表...")
    
    # 設定 API 請求頭 - Token 優先，其次 Global API Key（不建議）
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif api_key and email:
        headers["X-Auth-Email"] = email
        headers["X-Auth-Key"] = api_key
    else:
        raise Exception("缺少 api_token 或 api_key/email")
    
    zones = []
    page = 1
    per_page = 50
    
    while True:
        try:
            if account_id:
                url = f"https://api.cloudflare.com/client/v4/zones?page={page}&per_page={per_page}&account.id={account_id}"
            else:
                url = f"https://api.cloudflare.com/client/v4/zones?page={page}&per_page={per_page}"
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
    email = account.get("email", "unknown")
    token = account.get("api_token")
    api_key = account.get("api_key")
    
    # 設定 API 請求頭 - Token 優先，其次 Global API Key（不建議）
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif api_key and email:
        headers["X-Auth-Email"] = email
        headers["X-Auth-Key"] = api_key
    else:
        raise Exception("缺少 api_token 或 api_key/email")
    
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
def get_zone_metric(zone_id, zone_name, metric_name, account):
    email = account.get("email", "unknown")
    token = account.get("api_token")
    api_key = account.get("api_key")
    
    # 設定 API 請求頭 - Token 優先，其次 Global API Key（不建議）
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif api_key and email:
        headers["X-Auth-Email"] = email
        headers["X-Auth-Key"] = api_key
    else:
        raise Exception("缺少 api_token 或 api_key/email")
    
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
              httpRequests1dGroups(limit: 30, filter: {{date_geq: "{start_date}", date_lt: "{end_date}"}}) {{
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
            raise Exception(f"HTTP 狀態碼: {response.status_code}")
        
        data = response.json()
        
        # 檢查 GraphQL 錯誤
        if "errors" in data and data["errors"]:
            error_msg = data["errors"][0].get("message", "未知錯誤")
            raise Exception(f"GraphQL 錯誤: {error_msg}")
        
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
        
        email = account.get("email", "unknown")
        token = account.get("api_token")
        api_key = account.get("api_key")
        
        # 設定 API 請求頭 - Token 優先，其次 Global API Key（不建議）
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        elif api_key and email:
            headers["X-Auth-Email"] = email
            headers["X-Auth-Key"] = api_key
        else:
            raise Exception("缺少 api_token 或 api_key/email")
        
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
            query = f"""
            query {{
              viewer {{
                zones(filter: {{zoneTag: "{zone_id}"}}) {{
                  httpRequests1dGroups(limit: 30, filter: {{date_geq: "{start_date}", date_lt: "{end_date}"}}) {{
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
                data=json.dumps({"query": query})
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP 狀態碼: {response.status_code}")
            
            data = response.json()
            
            if "errors" in data and data["errors"]:
                error_msg = data["errors"][0].get("message", "未知錯誤")
                raise Exception(f"GraphQL 錯誤: {error_msg}")
            
            # 提取數據 - 簡化版
            try:
                records = data["data"]["viewer"]["zones"][0]["httpRequests1dGroups"]
                total_value = 0
                
                for entry in records:
                    if "sum" in entry and metric_name in entry["sum"]:
                        value = entry["sum"][metric_name]
                        total_value += value
                
                # 處理度量單位轉換
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
    
    # 定義輸出文件名
    results_csv = f"cloudflare_metrics_{timestamp}.csv"
    failed_domains_csv = f"cloudflare_failed_domains_{timestamp}.csv"
    
    print("開始獲取多個 Cloudflare 帳戶的域名資訊...")
    
    all_results = []
    
    # 為每個帳戶獲取域名信息
    for account in accounts:
        print(f"\n處理帳戶: {account['email']}...")
        
        # 獲取該帳戶的所有域名
        zones = get_all_zones(account)
        if not zones:
            print(f"帳戶 {account['email']} 沒有找到域名，或者獲取失敗")
            continue
        
        # 每批次處理10個域名
        batch_size = 10
        for i in range(0, len(zones), batch_size):
            batch = zones[i:i+batch_size]
            print(f"\n處理帳戶 {account['email']} 的第 {i+1} 到 {min(i+batch_size, len(zones))} 個域名 (共 {len(zones)} 個)...")
            
            batch_results = []
            
            for zone in batch:
                zone_id = zone["id"]
                zone_name = zone["name"]
                
                # 獲取計劃類型
                plan = get_zone_plan(zone_id, zone_name, account)
                
                # 分別獲取每個指標，並增加延遲
                bytes_total = get_zone_metric(zone_id, zone_name, "bytes", account)
                time.sleep(1)
                
                requests_count = get_zone_metric(zone_id, zone_name, "requests", account)
                time.sleep(1)
                
                cached_bytes = get_zone_metric(zone_id, zone_name, "cachedBytes", account)
                time.sleep(1)
                
                cached_requests = get_zone_metric(zone_id, zone_name, "cachedRequests", account)
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
                    "zone_id": zone_id
                })
            
            # 處理當前批次因速率限制而失敗的請求
            if rate_limited_requests:
                print(f"\n批次中有 {len(rate_limited_requests)} 個請求因速率限制而失敗，等待處理...")
                retry_results = process_rate_limited_requests()
                
                # 更新結果
                for result in batch_results:
                    zone_name = result["域名"]
                    
                    # 檢查並更新每個指標
                    if result["總請求數"] == "rate_limited":
                        key = f"{zone_name}_requests"
                        if key in retry_results:
                            result["總請求數"] = retry_results[key]
                    
                    if result["總流量(MB)"] == "rate_limited":
                        key = f"{zone_name}_bytes"
                        if key in retry_results:
                            result["總流量(MB)"] = retry_results[key]
                    
                    if result["緩存流量(MB)"] == "rate_limited":
                        key = f"{zone_name}_cachedBytes"
                        if key in retry_results:
                            result["緩存流量(MB)"] = retry_results[key]
                    
                    if result["緩存請求數"] == "rate_limited":
                        key = f"{zone_name}_cachedRequests"
                        if key in retry_results:
                            result["緩存請求數"] = retry_results[key]
                
                rate_limited_requests.clear()  # 清空處理過的請求
            
            # 添加批次結果到總結果
            all_results.extend(batch_results)
            
            # 將批次處理結果保存到文件
            if len(all_results) == len(batch_results):  # 如果是第一批結果
                save_results_to_csv(batch_results, results_csv, is_append=False)
            else:
                save_results_to_csv(batch_results, results_csv, is_append=True)
            
            # 每批次處理完後休息一下
            if i + batch_size < len(zones):
                print("批次處理完成，休息20秒避免速率限制...")
                time.sleep(20)
        
        # 每個帳戶處理完成後休息更長時間
        if account != accounts[-1]:  # 如果不是最後一個帳戶
            print(f"帳戶 {account['email']} 處理完成，休息60秒後處理下一個帳戶...")
            time.sleep(60)
    
    # 保存所有結果的摘要
    print("\n所有帳戶處理完成！")
    print(f"共處理了 {len(all_results)} 個域名")
    
    # 將所有域名按流量排序的總結果
    try:
        all_df = pd.DataFrame(all_results)
        if "zone_id" in all_df.columns:
            all_df = all_df.drop(columns=["zone_id"])
        
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
        print(f"\n共有 {len(failed_domains)} 個域名處理失敗")
        df_failed = pd.DataFrame(failed_domains)
        df_failed.to_csv(failed_domains_csv, index=False, encoding="utf-8-sig")
        print(f"失敗的域名已保存到 {failed_domains_csv}")
        print("\n失敗的域名列表:")
        print(df_failed[["帳戶", "域名", "操作", "失敗原因"]])

if __name__ == "__main__":
    main()