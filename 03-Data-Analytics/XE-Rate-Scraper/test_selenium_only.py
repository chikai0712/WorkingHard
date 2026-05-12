#!/usr/bin/env python3
"""
僅使用 Selenium 測試 XE.com 頁面（可視化）
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def test_selenium():
    """使用 Selenium 測試（可視化）"""
    print("=" * 60)
    print("🔍 使用 Selenium 測試 XE.com 頁面訪問")
    print("=" * 60)
    
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # 不使用 headless，可以看到瀏覽器
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        url = "https://app.xe.com/activity"
        print(f"\n🌐 正在訪問: {url}")
        driver.get(url)
        
        print("⏳ 等待頁面載入（15秒）...")
        time.sleep(15)
        
        # 檢查頁面標題
        title = driver.title
        print(f"\n📄 頁面標題: {title}")
        
        # 檢查當前 URL（可能被重定向）
        current_url = driver.current_url
        print(f"🔗 當前 URL: {current_url}")
        
        # 檢查是否有登入相關元素
        print("\n🔍 檢查登入相關元素...")
        login_keywords = ['login', 'sign in', '登入', 'log in', 'signin']
        found_login = False
        for keyword in login_keywords:
            try:
                # 查找包含關鍵字的元素
                xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]"
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"   ✅ 找到包含 '{keyword}' 的元素: {len(elements)} 個")
                    for elem in elements[:3]:
                        try:
                            text = elem.text[:100] if elem.text else "無文字"
                            print(f"      - {elem.tag_name}: {text}")
                            found_login = True
                        except:
                            pass
            except Exception as e:
                pass
        
        if not found_login:
            print("   ❌ 未找到明顯的登入元素")
        
        # 檢查頁面內容
        print("\n🔍 檢查頁面內容...")
        page_source = driver.page_source.lower()
        
        keywords = {
            'login': 'login' in page_source,
            'sign in': 'sign in' in page_source or 'signin' in page_source,
            'register': 'register' in page_source,
            'currency': 'currency' in page_source,
            'rate': 'rate' in page_source,
            'exchange': 'exchange' in page_source,
            'activity': 'activity' in page_source,
            'restricted': 'restricted' in page_source,
            'access denied': 'access denied' in page_source,
            'please log in': 'please log in' in page_source,
            'authentication': 'authentication' in page_source,
        }
        
        for key, found in keywords.items():
            status = "✅" if found else "❌"
            print(f"   {status} '{key}': {found}")
        
        # 檢查是否有表單
        try:
            forms = driver.find_elements(By.TAG_NAME, "form")
            if forms:
                print(f"\n📝 找到 {len(forms)} 個表單")
                for i, form in enumerate(forms[:3], 1):
                    action = form.get_attribute('action') or '無 action'
                    form_id = form.get_attribute('id') or '無 ID'
                    print(f"   表單 {i}: ID={form_id}, Action={action}")
        except:
            pass
        
        # 截圖保存
        screenshot_path = "xe_page_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"\n📸 頁面截圖已保存: {screenshot_path}")
        
        # 保存頁面源代碼
        html_path = "xe_page_source_selenium.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"📄 頁面源代碼已保存: {html_path}")
        
        # 檢查是否被重定向到登入頁面
        if 'login' in current_url.lower() or 'signin' in current_url.lower():
            print("\n⚠️  可能被重定向到登入頁面")
            print("   建議：需要登入才能訪問此頁面")
        elif 'activity' in current_url.lower():
            print("\n✅ URL 未改變，但可能內容需要登入後才能顯示")
        
        # 檢查頁面是否有內容
        body_text = driver.find_element(By.TAG_NAME, "body").text
        if len(body_text.strip()) < 100:
            print("\n⚠️  頁面內容很少，可能是：")
            print("   1. 需要登入才能看到內容")
            print("   2. 內容由 JavaScript 動態載入（需要更長等待時間）")
            print("   3. 頁面結構已改變")
        else:
            print(f"\n✅ 頁面有內容（{len(body_text)} 字元）")
            print("   前 200 字元預覽:")
            print(f"   {body_text[:200]}...")
        
        print("\n⏸️  瀏覽器將保持開啟 20 秒，請手動檢查...")
        print("   如果看到登入頁面，說明需要登入")
        print("   如果看到空白頁面，可能是 JavaScript 加載問題")
        time.sleep(20)
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔒 關閉瀏覽器...")
        driver.quit()

if __name__ == '__main__':
    test_selenium()

