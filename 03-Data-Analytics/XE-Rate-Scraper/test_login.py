#!/usr/bin/env python3
"""
測試 XE.com 登入功能
"""

import os
import sys
import getpass
from xe_scraper import XERateScraper

def main():
    print("=" * 60)
    print("🔐 XE.com 登入測試")
    print("=" * 60)
    
    # 獲取登入憑證
    email = os.getenv('XE_EMAIL')
    password = os.getenv('XE_PASSWORD')
    
    if not email:
        email = input("請輸入 XE.com Email: ").strip()
    
    if not password:
        password = getpass.getpass("請輸入 XE.com 密碼: ").strip()
    
    if not email or not password:
        print("❌ 未提供完整的登入憑證")
        sys.exit(1)
    
    print(f"\n📧 使用帳號: {email[:3]}***")
    print("🔐 正在測試登入...\n")
    
    # 使用非 headless 模式以便查看
    with XERateScraper(headless=False, email=email, password=password) as scraper:
        if scraper.login():
            print("\n" + "=" * 60)
            print("✅ 登入測試成功！")
            print("=" * 60)
            print("\n💡 提示：")
            print("   1. 瀏覽器將保持開啟，您可以查看登入後的頁面")
            print("   2. 按 Enter 關閉瀏覽器...")
            input()
        else:
            print("\n" + "=" * 60)
            print("❌ 登入測試失敗")
            print("=" * 60)
            print("\n💡 故障排除：")
            print("   1. 檢查帳號密碼是否正確")
            print("   2. 檢查是否需要驗證碼（目前不支援）")
            print("   3. 檢查帳號是否被鎖定")
            print("   4. 查看瀏覽器中的錯誤訊息")
            input("\n按 Enter 關閉瀏覽器...")
            sys.exit(1)

if __name__ == '__main__':
    main()

