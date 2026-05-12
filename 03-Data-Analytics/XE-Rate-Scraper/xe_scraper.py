#!/usr/bin/env python3
"""
XE.com 匯率抓取工具
抓取 https://app.xe.com/activity 的所有匯率數據
"""

import time
import json
import csv
import random
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium 未安裝，將嘗試使用 requests + BeautifulSoup")

import requests
from bs4 import BeautifulSoup
import os

# 嘗試載入 .env 檔案（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv 是可選的，如果未安裝則跳過


class XERateScraper:
    """XE.com 匯率抓取器"""
    
    BASE_URL = "https://app.xe.com/activity"
    
    def __init__(self, use_selenium: bool = True, headless: bool = True, email: Optional[str] = None, password: Optional[str] = None, use_cookies: bool = False):
        """
        初始化抓取器
        
        Args:
            use_selenium: 是否使用 Selenium（處理 JavaScript 渲染）
            headless: 是否使用無頭模式
            email: XE.com 帳號 Email（可選）
            password: XE.com 帳號密碼（可選）
            use_cookies: 是否使用保存的 cookies（優先於登入）
        """
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.headless = headless
        self.email = email
        self.password = password
        self.use_cookies = use_cookies
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
    def __enter__(self):
        """上下文管理器入口"""
        if self.use_selenium:
            self._init_selenium()
            # 如果使用 cookies，載入它們
            if self.use_cookies:
                self._load_cookies()
        return self
    
    def _load_cookies(self):
        """載入保存的 cookies"""
        cookies_file = Path("xe_cookies.json")
        if not cookies_file.exists():
            print("⚠️  Cookie 檔案不存在: xe_cookies.json")
            print("💡 請先執行: python3 manual_login_helper.py")
            return False
        
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            # 先訪問域名以設置 cookies
            self.driver.get("https://account.xe.com")
            time.sleep(2)
            
            # 添加 cookies
            for cookie in cookies:
                try:
                    # 移除可能導致問題的欄位
                    cookie.pop('sameSite', None)
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"   ⚠️  無法添加 cookie: {cookie.get('name', 'unknown')} - {e}")
            
            print(f"✅ 已載入 {len(cookies)} 個 cookies")
            return True
        except Exception as e:
            print(f"❌ 載入 cookies 時出錯: {e}")
            return False
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    def _init_selenium(self):
        """初始化 Selenium WebDriver"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 添加更多反檢測選項
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 執行反檢測腳本
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                '''
            })
            
            print("✅ Selenium WebDriver 初始化成功")
        except Exception as e:
            print(f"⚠️  Selenium 初始化失敗: {e}")
            print("   將嘗試使用 requests 方法")
            self.use_selenium = False
    
    def _human_type(self, element, text: str, delay_range: tuple = (0.05, 0.2)):
        """模擬人類輸入（逐字輸入，帶隨機延遲）"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(*delay_range))
    
    def _human_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """隨機延遲，模擬人類思考時間"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def close(self):
        """關閉瀏覽器驅動"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def login(self) -> bool:
        """登入 XE.com 帳號"""
        if not self.driver:
            print("❌ 瀏覽器未初始化，無法登入")
            return False
        
        if not self.email or not self.password:
            print("⚠️  未提供登入憑證（email 和 password）")
            return False
        
        try:
            # 訪問登入頁面
            login_url = "https://account.xe.com/signin"
            print(f"🔐 正在訪問登入頁面: {login_url}")
            self.driver.get(login_url)
            
            # 等待頁面載入
            print("⏳ 等待登入頁面載入...")
            time.sleep(5)
            
            # 查找 Email 輸入框
            try:
                # 嘗試多種選擇器
                email_selectors = [
                    (By.ID, "27-input"),  # 根據之前看到的 HTML
                    (By.NAME, "email"),
                    (By.CSS_SELECTOR, "input[type='email']"),
                    (By.CSS_SELECTOR, "input[data-testid='signin-email']"),
                    (By.XPATH, "//input[@type='email']"),
                ]
                
                email_input = None
                for by, selector in email_selectors:
                    try:
                        email_input = self.driver.find_element(by, selector)
                        if email_input:
                            print(f"   ✅ 找到 Email 輸入框: {by}={selector}")
                            break
                    except:
                        continue
                
                if not email_input:
                    print("   ❌ 無法找到 Email 輸入框")
                    return False
                
                # 填寫 Email（模擬人類輸入）
                print(f"   📝 正在輸入 Email: {self.email[:3]}***")
                self._human_type(email_input, self.email)
                self._human_delay(0.3, 0.8)  # 輸入後稍作停頓
                print(f"   ✅ 已填寫 Email")
                
            except Exception as e:
                print(f"   ❌ 填寫 Email 時出錯: {e}")
                return False
            
            # 查找 Password 輸入框
            try:
                password_selectors = [
                    (By.ID, "31-input"),  # 根據之前看到的 HTML
                    (By.NAME, "password"),
                    (By.CSS_SELECTOR, "input[type='password']"),
                    (By.CSS_SELECTOR, "input[data-testid='signin-password']"),
                    (By.XPATH, "//input[@type='password']"),
                ]
                
                password_input = None
                for by, selector in password_selectors:
                    try:
                        password_input = self.driver.find_element(by, selector)
                        if password_input:
                            print(f"   ✅ 找到 Password 輸入框: {by}={selector}")
                            break
                    except:
                        continue
                
                if not password_input:
                    print("   ❌ 無法找到 Password 輸入框")
                    return False
                
                # 填寫 Password（模擬人類輸入）
                print("   📝 正在輸入 Password...")
                self._human_type(password_input, self.password)
                self._human_delay(0.5, 1.5)  # 輸入密碼後稍作停頓
                print("   ✅ 已填寫 Password")
                
            except Exception as e:
                print(f"   ❌ 填寫 Password 時出錯: {e}")
                return False
            
            # 查找並點擊登入按鈕
            try:
                submit_selectors = [
                    (By.CSS_SELECTOR, "button[type='submit']"),
                    (By.XPATH, "//button[contains(text(), 'Continue')]"),
                    (By.XPATH, "//button[contains(text(), 'Sign in')]"),
                    (By.XPATH, "//button[contains(text(), '登入')]"),
                    (By.CSS_SELECTOR, ".submit-button"),
                ]
                
                submit_button = None
                for by, selector in submit_selectors:
                    try:
                        submit_button = self.driver.find_element(by, selector)
                        if submit_button and submit_button.is_enabled():
                            print(f"   ✅ 找到登入按鈕: {by}={selector}")
                            break
                    except:
                        continue
                
                if not submit_button:
                    print("   ❌ 無法找到登入按鈕")
                    return False
                
                # 點擊登入按鈕（使用 ActionChains 模擬真實點擊）
                print("   🔄 點擊登入按鈕...")
                self._human_delay(0.3, 0.8)  # 點擊前稍作停頓
                
                # 使用 ActionChains 移動到按鈕並點擊
                actions = ActionChains(self.driver)
                actions.move_to_element(submit_button).pause(random.uniform(0.1, 0.3)).click().perform()
                
                # 等待登入完成（檢查是否重定向或出現錯誤）
                print("   ⏳ 等待登入處理...")
                time.sleep(3)
                
                # 檢查是否需要處理驗證碼或其他安全機制
                try:
                    # 檢查是否有驗證碼
                    captcha_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        "iframe[src*='captcha'], .captcha, [data-captcha], #captcha")
                    if captcha_elements:
                        print("   ⚠️  檢測到驗證碼，需要手動處理")
                        if not self.headless:
                            print("   💡 請在瀏覽器中手動完成驗證碼驗證")
                            input("   完成後按 Enter 繼續...")
                        else:
                            print("   ❌ Headless 模式下無法處理驗證碼，請使用 --no-headless")
                            return False
                except:
                    pass
                
                # 再次等待
                time.sleep(3)
                
                # 檢查當前 URL
                current_url = self.driver.current_url
                print(f"   🔗 當前 URL: {current_url}")
                
                # 檢查是否需要 2FA（兩步驟驗證）
                if '2fa' in current_url.lower() or 'two-factor' in current_url.lower() or 'phone-validation' in current_url.lower():
                    print("   🔐 檢測到兩步驟驗證（2FA）")
                    if not self.headless:
                        print("   💡 請在瀏覽器中手動完成 2FA 驗證")
                        print("   💡 完成後，請回到終端機按 Enter 繼續...")
                        try:
                            input("   按 Enter 繼續...")
                        except (EOFError, KeyboardInterrupt):
                            print("   ⚠️  無法讀取輸入（非互動式環境）")
                            print("   💡 建議使用 cookies 方式：python3 manual_login_helper.py")
                            return False
                        
                        # 再次檢查 URL
                        current_url = self.driver.current_url
                        print(f"   🔗 當前 URL: {current_url}")
                        
                        if 'signin' not in current_url.lower() and 'login' not in current_url.lower() and '2fa' not in current_url.lower():
                            print("   ✅ 2FA 驗證完成，登入成功！")
                            return True
                        else:
                            print("   ⚠️  2FA 驗證可能未完成")
                            return False
                    else:
                        print("   ❌ Headless 模式下無法處理 2FA")
                        print("   💡 請使用 --no-headless 或改用 cookies 方式")
                        print("   💡 推薦：python3 manual_login_helper.py")
                        return False
                
                # 檢查是否登入成功（URL 應該改變，不再是 signin）
                if 'signin' not in current_url.lower() and 'login' not in current_url.lower():
                    print("   ✅ 登入成功！")
                    return True
                else:
                    # 檢查是否有錯誤訊息
                    try:
                        error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [role='alert']")
                        if error_elements:
                            error_text = error_elements[0].text
                            print(f"   ❌ 登入失敗: {error_text}")
                        else:
                            print("   ⚠️  可能仍在登入頁面，請檢查帳號密碼")
                    except:
                        print("   ⚠️  登入狀態不明，請手動檢查")
                    return False
                
            except Exception as e:
                print(f"   ❌ 點擊登入按鈕時出錯: {e}")
                import traceback
                traceback.print_exc()
                return False
                
        except Exception as e:
            print(f"❌ 登入過程中出錯: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def scrape_with_selenium(self) -> List[Dict]:
        """使用 Selenium 抓取匯率數據"""
        # 如果使用 cookies，跳過登入
        if self.use_cookies:
            print("🍪 使用保存的 cookies，跳過登入流程")
        # 如果需要登入，先執行登入
        elif self.email and self.password:
            print("\n" + "=" * 60)
            print("🔐 登入流程")
            print("=" * 60)
            login_success = self.login()
            if not login_success:
                print("⚠️  登入失敗，將嘗試繼續訪問頁面（可能無法獲取完整數據）")
            print("=" * 60 + "\n")
        
        print(f"🌐 正在訪問 {self.BASE_URL}...")
        self.driver.get(self.BASE_URL)
        
        # 等待頁面載入
        print("⏳ 等待頁面載入...")
        time.sleep(5)
        
        # 檢查是否被重定向到登入頁面或 2FA
        current_url = self.driver.current_url
        if 'signin' in current_url.lower() or 'login' in current_url.lower():
            print("⚠️  被重定向到登入頁面")
            if not self.email or not self.password:
                print("💡 提示: 請提供登入憑證（--email 和 --password）")
            else:
                print("💡 提示: 登入可能失敗，請檢查帳號密碼是否正確")
        elif '2fa' in current_url.lower() or 'two-factor' in current_url.lower():
            print("⚠️  需要完成 2FA 驗證")
            if not self.headless:
                print("💡 請在瀏覽器中完成 2FA 驗證")
                input("完成後按 Enter 繼續...")
                # 重新訪問目標頁面
                self.driver.get(self.BASE_URL)
                time.sleep(5)
            else:
                print("💡 請使用 --no-headless 或改用 cookies 方式")
        
        # 嘗試多種選擇器來找到匯率數據
        rates = []
        
        try:
            # 方法1: 查找表格
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            if tables:
                print(f"📊 找到 {len(tables)} 個表格")
                for table in tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    for row in rows[1:]:  # 跳過表頭
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:
                            rate_data = {
                                'currency_pair': cells[0].text.strip() if len(cells) > 0 else '',
                                'rate': cells[1].text.strip() if len(cells) > 1 else '',
                                'change': cells[2].text.strip() if len(cells) > 2 else '',
                                'timestamp': datetime.now().isoformat()
                            }
                            rates.append(rate_data)
            
            # 方法2: 查找包含匯率資訊的 div 或 span
            if not rates:
                print("🔍 嘗試查找其他格式的匯率數據...")
                # 查找包含貨幣代碼的元素
                currency_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'USD') or contains(text(), 'EUR') or contains(text(), 'GBP')]")
                
                # 查找包含數字的元素（可能是匯率）
                rate_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'rate') or contains(@class, 'price') or contains(@class, 'value')]")
                
                print(f"   找到 {len(currency_elements)} 個貨幣元素")
                print(f"   找到 {len(rate_elements)} 個可能的匯率元素")
            
            # 方法3: 獲取頁面源代碼並解析
            if not rates:
                print("📄 嘗試解析頁面源代碼...")
                page_source = self.driver.page_source
                rates = self._parse_html(page_source)
            
            # 方法4: 查找 JSON 數據
            if not rates:
                print("🔍 嘗試查找頁面中的 JSON 數據...")
                scripts = self.driver.find_elements(By.TAG_NAME, "script")
                for script in scripts:
                    script_text = script.get_attribute("innerHTML")
                    if script_text and ("rate" in script_text.lower() or "currency" in script_text.lower()):
                        try:
                            # 嘗試提取 JSON
                            import re
                            json_matches = re.findall(r'\{[^{}]*"rate"[^{}]*\}', script_text)
                            for match in json_matches:
                                try:
                                    data = json.loads(match)
                                    if 'rate' in data or 'currency' in data:
                                        rates.append(data)
                                except:
                                    pass
                        except:
                            pass
            
        except Exception as e:
            print(f"❌ 抓取過程中出錯: {e}")
            import traceback
            traceback.print_exc()
        
        return rates
    
    def scrape_with_requests(self) -> List[Dict]:
        """使用 requests 抓取匯率數據"""
        print(f"🌐 正在訪問 {self.BASE_URL}...")
        
        try:
            response = self.session.get(self.BASE_URL, timeout=30)
            response.raise_for_status()
            
            print("📄 解析 HTML...")
            rates = self._parse_html(response.text)
            
            return rates
        except Exception as e:
            print(f"❌ 請求失敗: {e}")
            return []
    
    def _parse_html(self, html: str) -> List[Dict]:
        """解析 HTML 內容提取匯率數據"""
        soup = BeautifulSoup(html, 'lxml')
        rates = []
        
        # 方法1: 查找表格
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])] if rows else []
            
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    rate_data = {
                        'currency_pair': cells[0].get_text(strip=True) if len(cells) > 0 else '',
                        'rate': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                        'change': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                        'timestamp': datetime.now().isoformat()
                    }
                    rates.append(rate_data)
        
        # 方法2: 查找包含貨幣代碼的文字
        if not rates:
            # 查找所有包含常見貨幣代碼的元素
            currency_codes = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'AUD', 'CAD', 'CHF', 'HKD', 'SGD']
            for code in currency_codes:
                elements = soup.find_all(string=lambda text: text and code in text)
                for elem in elements[:5]:  # 限制數量
                    parent = elem.parent
                    if parent:
                        rate_data = {
                            'currency_pair': code,
                            'rate': parent.get_text(strip=True),
                            'timestamp': datetime.now().isoformat()
                        }
                        rates.append(rate_data)
        
        # 方法3: 查找 script 標籤中的 JSON 數據
        scripts = soup.find_all('script', type='application/json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and ('rates' in data or 'currencies' in data):
                    # 處理嵌套的匯率數據
                    if 'rates' in data:
                        for pair, rate in data['rates'].items():
                            rates.append({
                                'currency_pair': pair,
                                'rate': str(rate),
                                'timestamp': datetime.now().isoformat()
                            })
            except:
                pass
        
        return rates
    
    def scrape(self) -> List[Dict]:
        """抓取匯率數據（自動選擇方法）"""
        if self.use_selenium:
            return self.scrape_with_selenium()
        else:
            return self.scrape_with_requests()
    
    def save_to_json(self, rates: List[Dict], filename: Optional[str] = None):
        """儲存數據到 JSON 檔案"""
        if filename is None:
            filename = f"xe_rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = Path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(rates, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 數據已儲存到: {filepath}")
        return filepath
    
    def save_to_csv(self, rates: List[Dict], filename: Optional[str] = None):
        """儲存數據到 CSV 檔案"""
        if filename is None:
            filename = f"xe_rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if not rates:
            print("⚠️  沒有數據可儲存")
            return None
        
        df = pd.DataFrame(rates)
        filepath = Path(filename)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        print(f"✅ 數據已儲存到: {filepath}")
        return filepath
    
    def save_to_excel(self, rates: List[Dict], filename: Optional[str] = None):
        """儲存數據到 Excel 檔案"""
        if filename is None:
            filename = f"xe_rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        if not rates:
            print("⚠️  沒有數據可儲存")
            return None
        
        df = pd.DataFrame(rates)
        filepath = Path(filename)
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        print(f"✅ 數據已儲存到: {filepath}")
        return filepath


def main():
    """主函數"""
    import argparse
    import os
    import getpass
    
    parser = argparse.ArgumentParser(description='XE.com 匯率抓取工具')
    parser.add_argument('--no-selenium', action='store_true', help='不使用 Selenium（僅使用 requests）')
    parser.add_argument('--no-headless', action='store_true', help='顯示瀏覽器視窗')
    parser.add_argument('--format', choices=['json', 'csv', 'excel', 'all'], default='all', help='輸出格式')
    parser.add_argument('--output', type=str, help='輸出檔案名稱（不含副檔名）')
    parser.add_argument('--email', type=str, help='XE.com 帳號 Email（或使用環境變數 XE_EMAIL）')
    parser.add_argument('--password', type=str, help='XE.com 帳號密碼（或使用環境變數 XE_PASSWORD，建議使用環境變數）')
    parser.add_argument('--use-cookies', action='store_true', help='使用保存的 cookies（優先於登入，需要先執行 manual_login_helper.py）')
    
    args = parser.parse_args()
    
    # 從環境變數或參數獲取登入憑證
    email = args.email or os.getenv('XE_EMAIL')
    password = args.password or os.getenv('XE_PASSWORD')
    
    # 如果沒有提供密碼，嘗試交互式輸入（僅在非 headless 模式下）
    if email and not password and not args.no_headless:
        try:
            password = getpass.getpass("請輸入 XE.com 密碼: ")
        except:
            print("⚠️  無法讀取密碼，將跳過登入")
            password = None
    
    print("=" * 60)
    print("🌐 XE.com 匯率抓取工具")
    print("=" * 60)
    
    if args.use_cookies:
        print("🍪 使用保存的 cookies 進行認證")
    elif email and password:
        print(f"📧 使用帳號: {email[:3]}***")
    elif email:
        print("⚠️  提供了 Email 但未提供密碼，將跳過登入")
    else:
        print("ℹ️  未提供登入憑證，將嘗試訪問公開頁面")
    
    with XERateScraper(use_selenium=not args.no_selenium, headless=not args.no_headless, email=email, password=password, use_cookies=args.use_cookies) as scraper:
        rates = scraper.scrape()
        
        if not rates:
            print("❌ 未能抓取到匯率數據")
            print("\n💡 提示:")
            print("   1. 檢查網路連接")
            print("   2. 網站可能需要登入或特殊權限")
            print("   3. 嘗試使用 --no-headless 查看瀏覽器行為")
            print("   4. 網站結構可能已更改，需要更新選擇器")
            return
        
        print(f"\n✅ 成功抓取 {len(rates)} 條匯率數據")
        print("\n📊 數據預覽:")
        for i, rate in enumerate(rates[:5], 1):
            print(f"   {i}. {rate}")
        if len(rates) > 5:
            print(f"   ... 還有 {len(rates) - 5} 條數據")
        
        # 儲存數據
        base_name = args.output if args.output else None
        
        if args.format in ['json', 'all']:
            json_file = base_name + '.json' if base_name else None
            scraper.save_to_json(rates, json_file)
        
        if args.format in ['csv', 'all']:
            csv_file = base_name + '.csv' if base_name else None
            scraper.save_to_csv(rates, csv_file)
        
        if args.format in ['excel', 'all']:
            excel_file = base_name + '.xlsx' if base_name else None
            try:
                scraper.save_to_excel(rates, excel_file)
            except ImportError:
                print("⚠️  需要安裝 openpyxl 才能匯出 Excel: pip install openpyxl")


if __name__ == '__main__':
    main()

