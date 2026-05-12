#!/usr/bin/env python3
"""
直接测试 Globalping API
"""
import asyncio
import httpx

TOKEN = "uh5vlg4ttg3v5gwby5zgtqrciimahql5"
API_URL = "https://api.globalping.io/v1/probes"

async def test_api():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print(f"🌐 测试 API: {API_URL}")
    print(f"📝 Token: {TOKEN[:20]}...")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            print("⏳ 发送请求...")
            response = await client.get(API_URL, headers=headers)
            
            print(f"✅ 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功获取 {len(data)} 个 probe")
                if data:
                    print(f"   第一个 probe: {data[0].get('location', {}).get('country')} - {data[0].get('location', {}).get('city')}")
            elif response.status_code == 403:
                print(f"❌ 403 Forbidden")
                print(f"   可能原因: Token 无效或已过期")
                print(f"   响应: {response.text[:200]}")
            else:
                print(f"⚠️  {response.status_code}")
                print(f"   响应: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ 错误: {e}")

asyncio.run(test_api())
