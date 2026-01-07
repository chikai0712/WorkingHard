#!/usr/bin/env python3
"""
測試 XE.com 頁面訪問權限
檢查是否需要登入或特殊權限
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests

def test_with_selenium():
    """使用 Selenium 測試（可視化）"""
    print("=" * 60)
    print("🔍 使用 Selenium 測試頁面訪問")
    print("=" * 60)
    
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # 不使用 headless，可以看到瀏覽器
    # chrome_options.add_argument('--headless')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        url = "https://app.xe.com/activity"
        print(f"\n🌐 正在訪問: {url}")
        driver.get(url)
        
        print("⏳ 等待頁面加載（10秒）...")
        time.sleep(10)
        
        # 檢查頁面標題
        title = driver.title
        print(f"\n📄 頁面標題: {title}")
        
        # 檢查當前 URL（可能被重定向）
        current_url = driver.current_url
        print(f"🔗 當前 URL: {current_url}")
        
        # 檢查是否有登入表單
        print("\n🔍 檢查登入相關元素...")
        try:
            login_form = driver.find_elements(By.TAG_NAME, "form")
            if login_form:
                print(f"   ✅ 找到 {len(login_form)} 個表單")
                for i, form in enumerate(login_form[:3], 1):
                    print(f"   表單 {i}: {form.get_attribute('action') or form.get_attribute('id') or '無 ID'}")
        except:
            print("   ⚠️  無法查找表單")
        
        # 檢查是否有登入按鈕或連結
        login_keywords = ['login', 'sign in', '登入', '登錄', 'log in']
        for keyword in login_keywords:
            try:
                elements = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                if elements:
                    print(f"   ✅ 找到包含 '{keyword}' 的元素: {len(elements)} 個")
                    for elem in elements[:3]:
                        print(f"      - {elem.tag_name}: {elem.text[:50]}")
            except:
                pass
        
        # 檢查頁面內容關鍵字
        print("\n🔍 檢查頁面內容關鍵字...")
        page_text = driver.page_source.lower()
        
        keywords = {
            'login': 'login' in page_text,
            'sign in': 'sign in' in page_text,
            'register': 'register' in page_text,
            'currency': 'currency' in page_text,
            'rate': 'rate' in page_text,
            'exchange': 'exchange' in page_text,
            'activity': 'activity' in page_text,
            'restricted': 'restricted' in page_text,
            'access denied': 'access denied' in page_text,
            'please log in': 'please log in' in page_text,
        }
        
        for key, found in keywords.items():
            status = "✅" if found else "❌"
            print(f"   {status} '{key}': {found}")
        
        # 截圖保存
        screenshot_path = "xe_page_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"\n📸 頁面截圖已保存: {screenshot_path}")
        
        # 保存頁面源代碼
        html_path = "xe_page_source.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"📄 頁面源代碼已保存: {html_path}")
        
        # 檢查 HTTP 狀態
        print("\n📊 頁面狀態:")
        print(f"   標題: {title}")
        print(f"   URL: {current_url}")
        if 'login' in current_url.lower() or 'signin' in current_url.lower():
            print("   ⚠️  可能被重定向到登入頁面")
        
        print("\n⏸️  瀏覽器將保持開啟 30 秒，請手動檢查...")
        print("   按 Ctrl+C 提前結束")
        time.sleep(30)
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

def test_with_requests():
    """使用 requests 測試（快速）"""
    print("\n" + "=" * 60)
    print("🔍 使用 requests 測試頁面訪問")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    try:
        url = "https://app.xe.com/activity"
        print(f"\n🌐 正在訪問: {url}")
        response = session.get(url, timeout=30, allow_redirects=True)
        
        print(f"\n📊 HTTP 狀態:")
        print(f"   狀態碼: {response.status_code}")
        print(f"   最終 URL: {response.url}")
        print(f"   重定向次數: {len(response.history)}")
        
        if response.history:
            print("   重定向鏈:")
            for i, resp in enumerate(response.history, 1):
                print(f"     {i}. {resp.status_code} -> {resp.url}")
        
        # 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title')
        print(f"\n📄 頁面標題: {title.text if title else '無標題'}")
        
        # 檢查關鍵字
        text_lower = response.text.lower()
        keywords = {
            'login': 'login' in text_lower,
            'sign in': 'sign in' in text_lower,
            'register': 'register' in text_lower,
            'currency': 'currency' in text_lower,
            'rate': 'rate' in text_lower,
        }
        
        print("\n🔍 頁面內容關鍵字:")
        for key, found in keywords.items():
            status = "✅" if found else "❌"
            print(f"   {status} '{key}': {found}")
        
        # 保存 HTML
        html_path = "xe_page_source_requests.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\n📄 頁面源代碼已保存: {html_path}")
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🚀 XE.com 頁面訪問權限測試")
    print("=" * 60)
    
    # 先測試 requests（快速）
    test_with_requests()
    
    print("\n" + "=" * 60)
    print("⚠️  接下來將使用 Selenium 打開瀏覽器（可視化測試）")
    print("   這將需要一些時間...")
    print("=" * 60)
    
    # 自動繼續（非交互模式）
    import sys
    if sys.stdin.isatty():
        try:
            input("\n按 Enter 繼續（或 Ctrl+C 取消）...")
        except (EOFError, KeyboardInterrupt):
            print("\n⏭️  跳過 Selenium 測試")
            sys.exit(0)
    
    # 再測試 Selenium（可視化）
    test_with_selenium()

