#!/usr/bin/env python3
"""
Globalping API 測試 - 使用正確的 payload 格式
"""
import requests
import json
import sys

TOKEN = "uh5vlg4ttg3v5gwby5zgtqrciimahql5"
API_URL = "https://api.globalping.io/v1"

def test_correct_format():
    """使用正確的 payload 格式測試"""
    print("\n" + "=" * 60)
    print("🔍 測試正確的 Payload 格式")
    print("=" * 60)
    
    # 正確的 payload 格式（不包含 options）
    payload = {
        "type": "http",
        "target": "example.com",
        "limit": 3,
        "locations": [{"country": "ID"}]
    }
    
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    
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
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 202:
            print("\n✅ 測量創建成功！")
            data = response.json()
            measure_id = data.get("id")
            print(f"Measurement ID: {measure_id}")
            
            # 嘗試獲取結果
            if measure_id:
                print(f"\n⏳ 等待 5 秒後獲取結果...")
                import time
                time.sleep(5)
                
                result_response = requests.get(
                    f"{API_URL}/measurements/{measure_id}",
                    headers={
                        "Authorization": f"Bearer {TOKEN}",
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                
                print(f"\nResult Status Code: {result_response.status_code}")
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    print(f"Result:")
                    print(json.dumps(result_data, indent=2)[:500])
                    print("\n✅ 成功獲取測量結果！")
                    return True
        else:
            print(f"\n❌ 創建失敗: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("🚀 Globalping API 正確格式測試")
    print("=" * 60)
    print(f"Token: {TOKEN[:20]}...")
    print(f"API URL: {API_URL}")
    
    success = test_correct_format()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ API 測試成功！應用可以正常工作")
    else:
        print("❌ API 測試失敗，請檢查 Token 或網絡")
    print("=" * 60 + "\n")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
