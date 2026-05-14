#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mlytics API 進階測試腳本
嘗試不同的 Base URL 和認證方式組合
"""

import requests
import json

MLYTICS_API_KEY = "wcHGixTn6JFE7C5XVI0yJgfFWlbzeJERfSqkRHfCP2lze7oJEv"

# 嘗試不同的 Base URL
base_urls = [
    "https://api.mlytics.com/v1",
    "https://api.mlytics.com",
    "https://api.mlytics.io/v1",
    "https://api.mlytics.io",
    "https://mlytics.com/api/v1",
    "https://mlytics.com/api",
]

# 嘗試不同的認證方式
def get_auth_headers_variants(api_key):
    """生成多種認證 Header 變體"""
    variants = []
    
    # 1. Bearer Token
    variants.append({
        "name": "Bearer Token",
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    })
    
    # 2. X-API-Key
    variants.append({
        "name": "X-API-Key Header",
        "headers": {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }
    })
    
    # 3. API-Key (不同的 Header 名稱)
    variants.append({
        "name": "API-Key Header",
        "headers": {
            "API-Key": api_key,
            "Content-Type": "application/json",
        }
    })
    
    # 4. apikey (小寫)
    variants.append({
        "name": "apikey Header (lowercase)",
        "headers": {
            "apikey": api_key,
            "Content-Type": "application/json",
        }
    })
    
    # 5. X-Api-Key (駝峰式)
    variants.append({
        "name": "X-Api-Key Header (camelCase)",
        "headers": {
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        }
    })
    
    # 6. 組合方式
    variants.append({
        "name": "X-API-Key + Bearer",
        "headers": {
            "X-API-Key": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    })
    
    return variants

# 測試的端點
test_endpoints = [
    "/health",
    "/status",
    "/",
    "/domains",
    "/zones",
    "/account",
    "/me",
]

def test_combination(base_url, auth_variant, endpoint):
    """測試特定的 Base URL + 認證方式 + 端點組合"""
    url = f"{base_url}{endpoint}"
    
    try:
        response = requests.get(url, headers=auth_variant["headers"], timeout=10)
        
        result = {
            "url": url,
            "status_code": response.status_code,
            "success": response.status_code in [200, 201, 202],
        }
        
        # 嘗試解析 JSON
        try:
            result["data"] = response.json()
        except:
            result["data"] = response.text[:200]
        
        return result
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }

def main():
    print("="*80)
    print("🔬 Mlytics API 進階測試 - 嘗試不同的 Base URL 和認證方式")
    print("="*80)
    print(f"API Key: {MLYTICS_API_KEY[:20]}...{MLYTICS_API_KEY[-10:]}\n")
    
    auth_variants = get_auth_headers_variants(MLYTICS_API_KEY)
    
    successful_combinations = []
    
    for base_url in base_urls:
        print(f"\n{'='*80}")
        print(f"🌐 測試 Base URL: {base_url}")
        print(f"{'='*80}")
        
        for auth_variant in auth_variants:
            print(f"\n  🔑 認證方式: {auth_variant['name']}")
            
            # 只測試幾個關鍵端點
            for endpoint in ["/health", "/domains", "/"]:
                result = test_combination(base_url, auth_variant, endpoint)
                
                status_icon = "✅" if result.get("success") else "❌"
                status_code = result.get("status_code", "N/A")
                
                print(f"    {status_icon} {endpoint}: {status_code}", end="")
                
                if result.get("success"):
                    print(" ✅ 成功！")
                    successful_combinations.append({
                        "base_url": base_url,
                        "auth": auth_variant["name"],
                        "endpoint": endpoint,
                        "result": result
                    })
                    # 顯示成功的響應
                    if isinstance(result.get("data"), dict):
                        print(f"      響應: {json.dumps(result['data'], indent=6, ensure_ascii=False)[:300]}")
                elif status_code == 401:
                    print(" (認證失敗)")
                elif status_code == 403:
                    print(" (權限不足)")
                elif status_code == 404:
                    print(" (端點不存在)")
                else:
                    error = result.get("error", "")
                    if error:
                        print(f" ({error[:50]})")
                    else:
                        print("")
                
                # 避免請求過快
                import time
                time.sleep(0.3)
    
    # 總結
    print(f"\n{'='*80}")
    print("📊 測試結果總結")
    print(f"{'='*80}")
    
    if successful_combinations:
        print(f"\n✅ 找到 {len(successful_combinations)} 個成功的組合：\n")
        for combo in successful_combinations:
            print(f"  • Base URL: {combo['base_url']}")
            print(f"    認證方式: {combo['auth']}")
            print(f"    端點: {combo['endpoint']}")
            print(f"    狀態碼: {combo['result'].get('status_code')}\n")
    else:
        print("\n❌ 沒有找到成功的組合")
        print("\n建議：")
        print("1. 確認 API Key 是否正確且有效")
        print("2. 檢查 Mlytics 控制台中的 API 文檔")
        print("3. 確認是否需要額外的認證參數（如 API Secret）")
        print("4. 聯繫 Mlytics 技術支援確認 API Base URL 和認證方式")
    
    print("="*80)

if __name__ == "__main__":
    main()

