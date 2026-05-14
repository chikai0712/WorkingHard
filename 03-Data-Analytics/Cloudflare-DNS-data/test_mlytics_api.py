#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mlytics API 測試腳本
用於測試 Mlytics API 連接、認證和端點是否正確
"""

import requests
import json
import sys
import time

# ============================================
# Mlytics API 配置（從 mlytics_report.py 複製）
# ============================================
MLYTICS_API_BASE_URL = "https://api.mlytics.com/v1"
MLYTICS_API_KEY = "wcHGixTn6JFE7C5XVI0yJgfFWlbzeJERfSqkRHfCP2lze7oJEv"
MLYTICS_API_SECRET = ""

# 測試帳戶資訊
account = {
    "account_id": "ck.chiu@unition.global",
    "api_key": MLYTICS_API_KEY,
    "api_secret": MLYTICS_API_SECRET,
    "email": "ck.chiu@unition.global"
}

# ============================================
# 測試函數
# ============================================

def get_headers(use_bearer=False, use_basic_auth=False, use_custom_header=True):
    """
    生成不同的認證 Header 進行測試
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    if use_custom_header:
        # 方式 1: 使用 X-API-Key Header
        headers["X-API-Key"] = account["api_key"]
        if account.get("api_secret"):
            headers["X-API-Secret"] = account["api_secret"]
    
    if use_bearer:
        # 方式 2: 使用 Bearer Token
        headers["Authorization"] = f"Bearer {account['api_key']}"
        if "X-API-Key" in headers:
            del headers["X-API-Key"]
    
    if use_basic_auth:
        # 方式 3: 使用 Basic Auth
        import base64
        credentials = f"{account['api_key']}:{account.get('api_secret', '')}"
        encoded = base64.b64encode(credentials.encode()).decode()
        headers["Authorization"] = f"Basic {encoded}"
        if "X-API-Key" in headers:
            del headers["X-API-Key"]
    
    return headers

def test_api_endpoint(url, headers, method="GET", params=None, data=None, description=""):
    """
    測試 API 端點
    """
    print(f"\n{'='*70}")
    print(f"🔍 測試: {description}")
    print(f"{'='*70}")
    print(f"URL: {url}")
    print(f"Method: {method}")
    print(f"Headers: {json.dumps({k: v[:20] + '...' if len(str(v)) > 20 else v for k, v in headers.items()}, indent=2)}")
    if params:
        print(f"Params: {json.dumps(params, indent=2)}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        else:
            print(f"❌ 不支援的 HTTP 方法: {method}")
            return None
        
        print(f"\n📊 響應狀態碼: {response.status_code}")
        print(f"📊 響應 Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'content-length', 'x-ratelimit', 'x-api-version']:
                print(f"   {key}: {value}")
        
        # 嘗試解析 JSON
        try:
            response_data = response.json()
            print(f"\n✅ JSON 響應（格式化）:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False)[:2000])  # 限制輸出長度
            if len(json.dumps(response_data, ensure_ascii=False)) > 2000:
                print("\n... (響應內容過長，已截斷)")
            
            return {
                "status_code": response.status_code,
                "data": response_data,
                "success": response.status_code in [200, 201, 202]
            }
        except json.JSONDecodeError:
            print(f"\n⚠️  響應不是有效的 JSON")
            print(f"原始響應內容（前500字元）:")
            print(response.text[:500])
            return {
                "status_code": response.status_code,
                "data": response.text,
                "success": False
            }
    
    except requests.exceptions.Timeout:
        print(f"\n❌ 請求超時")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 連接錯誤: {str(e)}")
        return None
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*70)
    print("🧪 Mlytics API 測試腳本")
    print("="*70)
    print(f"API Base URL: {MLYTICS_API_BASE_URL}")
    print(f"API Key: {MLYTICS_API_KEY[:20]}...{MLYTICS_API_KEY[-10:]}")
    print(f"帳戶 Email: {account['email']}")
    print("="*70)
    
    # 測試結果收集
    test_results = []
    
    # ============================================
    # 測試 1: 測試基礎連接（常見的根端點或健康檢查端點）
    # ============================================
    test_endpoints = [
        # 常見的 API 根端點
        ("/", "GET", None, None, "API 根端點"),
        ("/health", "GET", None, None, "健康檢查端點"),
        ("/status", "GET", None, None, "狀態端點"),
        ("/v1/health", "GET", None, None, "v1 健康檢查"),
    ]
    
    # ============================================
    # 測試 2: 測試不同的認證方式
    # ============================================
    auth_methods = [
        ("X-API-Key Header", True, False, False),
        ("Bearer Token", False, True, False),
        # ("Basic Auth", False, False, True),  # 如果不需要可以註解
    ]
    
    # ============================================
    # 測試 3: 測試常見的 API 端點
    # ============================================
    common_endpoints = [
        # 域名相關端點
        ("/domains", "GET", None, None, "獲取域名列表"),
        ("/zones", "GET", None, None, "獲取 Zones 列表"),
        ("/projects", "GET", None, None, "獲取項目列表"),
        ("/sites", "GET", None, None, "獲取站點列表"),
        
        # 統計相關端點
        ("/analytics", "GET", None, None, "獲取統計數據"),
        ("/stats", "GET", None, None, "獲取統計資訊"),
        ("/metrics", "GET", None, None, "獲取指標"),
        
        # DNS 相關端點
        ("/dns", "GET", None, None, "DNS 相關端點"),
        ("/dns/analytics", "GET", None, None, "DNS 統計"),
        
        # 帳戶相關端點
        ("/account", "GET", None, None, "獲取帳戶資訊"),
        ("/user", "GET", None, None, "獲取用戶資訊"),
        ("/me", "GET", None, None, "獲取當前用戶資訊"),
    ]
    
    # ============================================
    # 執行測試
    # ============================================
    
    # 首先測試基礎連接（使用 X-API-Key）
    print("\n" + "="*70)
    print("📋 階段 1: 測試基礎連接和認證")
    print("="*70)
    
    headers_x_api_key = get_headers(use_custom_header=True)
    
    for endpoint, method, params, data, desc in test_endpoints:
        url = f"{MLYTICS_API_BASE_URL}{endpoint}"
        result = test_api_endpoint(url, headers_x_api_key, method, params, data, desc)
        if result:
            test_results.append((endpoint, result))
            if result["success"]:
                print(f"✅ 端點 {endpoint} 測試成功！")
                break  # 找到可用的端點就停止
        time.sleep(1)  # 避免請求過快
    
    # 測試不同的認證方式
    print("\n" + "="*70)
    print("📋 階段 2: 測試不同的認證方式")
    print("="*70)
    
    test_endpoint = "/domains"  # 使用最常見的端點測試認證
    for auth_name, use_custom, use_bearer, use_basic in auth_methods:
        headers = get_headers(use_custom_header=use_custom, use_bearer=use_bearer, use_basic_auth=use_basic)
        url = f"{MLYTICS_API_BASE_URL}{test_endpoint}"
        result = test_api_endpoint(url, headers, "GET", None, None, f"測試認證方式: {auth_name}")
        if result:
            test_results.append((test_endpoint, result))
        time.sleep(1)
    
    # 測試常見的 API 端點
    print("\n" + "="*70)
    print("📋 階段 3: 測試常見的 API 端點")
    print("="*70)
    
    # 使用最可能成功的認證方式
    headers = get_headers(use_custom_header=True)
    
    for endpoint, method, params, data, desc in common_endpoints:
        url = f"{MLYTICS_API_BASE_URL}{endpoint}"
        result = test_api_endpoint(url, headers, method, params, data, desc)
        if result:
            test_results.append((endpoint, result))
            if result["success"]:
                print(f"✅ 找到可用的端點: {endpoint}")
        time.sleep(0.5)  # 避免請求過快
    
    # ============================================
    # 測試結果總結
    # ============================================
    print("\n" + "="*70)
    print("📊 測試結果總結")
    print("="*70)
    
    successful_tests = [r for r in test_results if r[1] and r[1].get("success")]
    failed_tests = [r for r in test_results if r[1] and not r[1].get("success")]
    
    print(f"\n✅ 成功的測試: {len(successful_tests)}")
    for endpoint, result in successful_tests:
        print(f"   - {endpoint} (狀態碼: {result['status_code']})")
    
    print(f"\n❌ 失敗的測試: {len(failed_tests)}")
    for endpoint, result in failed_tests:
        status_code = result.get('status_code', 'N/A')
        print(f"   - {endpoint} (狀態碼: {status_code})")
    
    # 提供建議
    print("\n" + "="*70)
    print("💡 建議")
    print("="*70)
    
    if successful_tests:
        print("✅ 找到可用的 API 端點！")
        print("\n請查看上面的響應內容，了解實際的 API 響應格式。")
        print("然後您可以根據實際響應格式調整 mlytics_report.py 中的解析邏輯。")
        
        # 顯示第一個成功響應的結構建議
        first_success = successful_tests[0]
        endpoint, result = first_success
        data = result.get("data", {})
        
        if isinstance(data, dict):
            print(f"\n📝 端點 {endpoint} 的響應結構示例:")
            print(f"   - 響應類型: {type(data).__name__}")
            print(f"   - 頂層鍵: {list(data.keys())[:10]}")
            
            # 嘗試找到數據列表
            for key in ['data', 'results', 'domains', 'zones', 'items', 'list']:
                if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                    print(f"\n   - 發現列表欄位 '{key}'，包含 {len(data[key])} 個項目")
                    if len(data[key]) > 0:
                        print(f"   - 第一個項目的結構: {list(data[key][0].keys())[:10]}")
                    break
    else:
        print("❌ 沒有找到可用的 API 端點。")
        print("\n可能的原因：")
        print("1. API Base URL 不正確")
        print("2. API Key 無效或認證方式不正確")
        print("3. API 端點路徑不正確")
        print("4. 需要其他認證參數（如 API Secret）")
        print("\n建議：")
        print("1. 檢查 Mlytics API 文檔，確認正確的 Base URL 和端點")
        print("2. 確認 API Key 是否正確")
        print("3. 確認是否需要 API Secret 或其他認證資訊")
        print("4. 檢查是否需要特定的 Header 或參數")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    import time
    main()

