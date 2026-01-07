#!/usr/bin/env python3
"""
手動登入輔助工具
用於手動登入後保存 cookies，供後續自動化使用
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from pathlib import Path

def save_cookies():
    """手動登入並保存 cookies"""
    print("=" * 60)
    print("🍪 XE.com Cookie 保存工具")
    print("=" * 60)
    print("\n此工具將：")
    print("1. 打開瀏覽器")
    print("2. 請您手動登入 XE.com")
    print("3. 保存登入後的 cookies")
    print("4. 後續自動化腳本可以使用這些 cookies\n")
    
    input("按 Enter 開始...")
    
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 訪問登入頁面
        print("\n🌐 正在打開登入頁面...")
        driver.get("https://account.xe.com/signin")
        
        print("\n" + "=" * 60)
        print("📝 請在瀏覽器中手動完成登入")
        print("=" * 60)
        print("\n步驟：")
        print("1. 在瀏覽器中輸入您的 Email 和密碼")
        print("2. 點擊登入按鈕")
        print("3. 如果出現 2FA（兩步驟驗證）：")
        print("   - 檢查您的手機簡訊")
        print("   - 在瀏覽器中輸入收到的驗證碼")
        print("   - 完成驗證")
        print("4. 確認已成功登入（應該能看到 XE.com 的主頁或活動頁面）")
        print("\n💡 提示：")
        print("   - 驗證碼通常會在幾秒內發送到您的手機")
        print("   - 請在瀏覽器中輸入驗證碼完成驗證")
        print("   - 完成所有步驟後，回到終端機按 Enter")
        print("\n完成登入後，請回到終端機...")
        
        input("\n✅ 已完成登入（包括 2FA 驗證）？按 Enter 繼續...")
        
        # 檢查是否已登入
        current_url = driver.current_url
        print(f"\n🔗 當前 URL: {current_url}")
        
        if 'signin' in current_url.lower() or 'login' in current_url.lower():
            print("⚠️  似乎仍在登入頁面，請確認已成功登入")
            response = input("是否仍要保存 cookies？(y/n): ")
            if response.lower() != 'y':
                print("❌ 已取消")
                return
        
        # 獲取 cookies
        cookies = driver.get_cookies()
        
        if not cookies:
            print("❌ 未獲取到 cookies")
            return
        
        # 保存 cookies
        cookies_file = Path("xe_cookies.json")
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Cookies 已保存到: {cookies_file}")
        print(f"   共保存 {len(cookies)} 個 cookies")
        print("\n💡 現在您可以在自動化腳本中使用這些 cookies")
        print("   執行: python3 xe_scraper.py --use-cookies")
        
    except KeyboardInterrupt:
        print("\n\n❌ 已取消")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n按 Enter 關閉瀏覽器...")
        input()
        driver.quit()

if __name__ == '__main__':
    save_cookies()

