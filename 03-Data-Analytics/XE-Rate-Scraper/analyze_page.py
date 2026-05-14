#!/usr/bin/env python3
"""
分析 XE.com 頁面，檢查是否需要登入
"""

import requests
from bs4 import BeautifulSoup
import json
import re

def analyze_page():
    """分析頁面內容"""
    print("=" * 60)
    print("🔍 分析 XE.com 頁面訪問要求")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    url = "https://app.xe.com/activity"
    
    try:
        print(f"\n🌐 訪問: {url}")
        response = session.get(url, timeout=30, allow_redirects=True)
        
        print(f"📊 HTTP 狀態: {response.status_code}")
        print(f"🔗 最終 URL: {response.url}")
        
        # 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 檢查標題
        title = soup.find('title')
        print(f"📄 頁面標題: {title.text if title and title.text else '（空）'}")
        
        # 檢查是否為 SPA
        scripts = soup.find_all('script', src=True)
        module_scripts = [s for s in scripts if s.get('type') == 'module']
        
        if module_scripts:
            print(f"\n✅ 這是單頁應用（SPA）")
            print(f"   找到 {len(module_scripts)} 個 JavaScript 模組")
            print("   ⚠️  內容需要 JavaScript 渲染才能顯示")
        
        # 檢查 noscript 標籤
        noscript = soup.find('noscript')
        if noscript:
            print(f"\n📝 noscript 內容:")
            print(f"   {noscript.get_text()[:200]}")
        
        # 檢查 body 內容
        body = soup.find('body')
        if body:
            body_text = body.get_text(strip=True)
            print(f"\n📄 Body 文字內容長度: {len(body_text)} 字元")
            
            if len(body_text) < 100:
                print("   ⚠️  內容很少，可能是：")
                print("      1. 需要 JavaScript 渲染")
                print("      2. 需要登入才能看到內容")
            else:
                print(f"   前 300 字元: {body_text[:300]}")
        
        # 檢查是否有 API 端點
        print("\n🔍 檢查可能的 API 端點...")
        text = response.text
        
        # 查找常見的 API 模式
        api_patterns = [
            r'["\']([^"\']*api[^"\']*)["\']',
            r'["\']([^"\']*\/v\d+\/[^"\']*)["\']',
            r'fetch\(["\']([^"\']*)["\']',
            r'axios\.(get|post)\(["\']([^"\']*)["\']',
        ]
        
        found_apis = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    found_apis.update(match)
                else:
                    found_apis.add(match)
        
        if found_apis:
            print(f"   找到 {len(found_apis)} 個可能的 API 端點:")
            for api in list(found_apis)[:10]:
                if api and len(api) > 5:
                    print(f"      - {api}")
        
        # 檢查是否需要認證
        print("\n🔍 檢查認證相關內容...")
        auth_keywords = {
            'login': text.lower().count('login'),
            'signin': text.lower().count('signin'),
            'sign in': text.lower().count('sign in'),
            'authenticate': text.lower().count('authenticate'),
            'auth': text.lower().count('auth'),
            'token': text.lower().count('token'),
            'session': text.lower().count('session'),
            'cookie': text.lower().count('cookie'),
        }
        
        total_auth = sum(auth_keywords.values())
        if total_auth > 0:
            print(f"   ⚠️  找到認證相關關鍵字（總計 {total_auth} 次）:")
            for key, count in auth_keywords.items():
                if count > 0:
                    print(f"      - '{key}': {count} 次")
            print("\n   💡 建議：此頁面可能需要登入")
        else:
            print("   ✅ 未找到明顯的認證關鍵字")
        
        # 檢查重定向
        if response.history:
            print(f"\n🔄 發生 {len(response.history)} 次重定向:")
            for i, resp in enumerate(response.history, 1):
                print(f"   {i}. {resp.status_code} -> {resp.url}")
        
        # 檢查 cookies
        cookies = session.cookies
        if cookies:
            print(f"\n🍪 Cookies ({len(cookies)} 個):")
            for cookie in cookies:
                print(f"   - {cookie.name}: {cookie.value[:50]}...")
        else:
            print("\n🍪 無 Cookies")
        
        # 總結
        print("\n" + "=" * 60)
        print("📊 分析總結")
        print("=" * 60)
        
        if module_scripts:
            print("✅ 這是單頁應用（SPA），需要 JavaScript 渲染")
        
        if total_auth > 10:
            print("⚠️  強烈建議：此頁面可能需要登入")
        elif total_auth > 0:
            print("⚠️  可能：此頁面可能需要登入")
        else:
            print("✅ 未發現明顯的登入要求")
        
        print("\n💡 建議測試方法：")
        print("   1. 使用 Selenium 等待 JavaScript 載入完成")
        print("   2. 檢查頁面是否有登入表單")
        print("   3. 嘗試訪問 XE.com 的公開 API（如果有的話）")
        print("   4. 查看瀏覽器開發者工具的 Network 標籤")
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    analyze_page()

