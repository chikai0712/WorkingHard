#!/usr/bin/env python3
"""
Globalping API 手動測試工具
在允許外網訪問的環境中運行

使用方法:
  python3 test_api_manual.py
"""
import requests
import json
import sys
from datetime import datetime

TOKEN = "uh5vlg4ttg3v5gwby5zgtqrciimahql5"
API_URL = "https://api.globalping.io/v1"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def print_result(response, title="Response"):
    print(f"\n{title}:")
    print(f"  Status Code: {response.status_code}")
    print(f"  Headers: {dict(response.headers)}")
    try:
        data = response.json()
        print(f"  Body: {json.dumps(data, indent=2)[:500]}")
    except:
        print(f"  Body: {response.text[:500]}")

def test_limits():
    """測試 API 額度"""
    print_section("1. 測試 API 額度 (/limits)")
    
    try:
        response = requests.get(
            f"{API_URL}/limits",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        print_result(response, "Limits Response")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API 連接成功！")
            print(f"  Token 有效")
            if 'rateLimit' in data:
                rate_limit = data['rateLimit']
                print(f"  Rate Limit: {json.dumps(rate_limit, indent=4)}")
            return True
        else:
            print(f"\n❌ API 返回錯誤: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ 連接失敗: {e}")
        return False

def test_create_measurement():
    """測試創建測量"""
    print_section("2. 測試創建測量 (/measurements)")
    
    payload = {
        "type": "http",
        "target": "example.com",
        "inProgressUpdates": False,
        "options": {
            "method": "HEAD"
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/measurements",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )
        print_result(response, "Create Measurement Response")
        
        if response.status_code in [200, 201]:
            print("\n✅ 測量創建成功！")
            data = response.json()
            if 'id' in data:
                print(f"  Measurement ID: {data['id']}")
            return True
        else:
            print(f"\n❌ 創建失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ 連接失敗: {e}")
        return False

def test_get_measurements():
    """測試獲取測量結果"""
    print_section("3. 測試獲取測量結果 (/measurements)")
    
    try:
        response = requests.get(
            f"{API_URL}/measurements?limit=1",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        print_result(response, "Get Measurements Response")
        
        if response.status_code == 200:
            print("\n✅ 獲取測量結果成功！")
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"  最近測量數: {len(data)}")
                print(f"  第一個測量: {json.dumps(data[0], indent=2)[:300]}")
            return True
        else:
            print(f"\n❌ 獲取失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ 連接失敗: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("🚀 Globalping API 手動測試工具")
    print("=" * 60)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Token: {TOKEN[:20]}...")
    print(f"API URL: {API_URL}")
    
    results = {
        "limits": test_limits(),
        "create_measurement": test_create_measurement(),
        "get_measurements": test_get_measurements()
    }
    
    print("\n" + "=" * 60)
    print("📊 測試總結")
    print("=" * 60)
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("✅ 所有測試通過！API 可以正常使用" if all_passed else "❌ 部分測試失敗，請檢查 Token 或網絡連接"))
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
