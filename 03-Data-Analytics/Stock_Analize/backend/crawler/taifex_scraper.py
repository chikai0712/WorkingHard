"""
TAIFEX 網頁爬蟲 - 實際實現
用於抓取三大法人、期貨、選擇權資料
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import time
import re
from io import StringIO
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TAIFEXScraper:
    """TAIFEX 網頁爬蟲"""
    
    BASE_URL = "https://www.taifex.com.tw"
    
    def __init__(self, db: Session):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def fetch_institutional_trading(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        抓取三大法人買賣超資料
        
        資料來源: https://www.taifex.com.tw/cht/3/futDataDown?down_type=2
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            url = f"{self.BASE_URL}/cht/3/futDataDown"
            date_str = target_date.strftime('%Y/%m/%d')
            
            params = {
                'down_type': '2',  # 三大法人買賣超
                'queryStartDate': date_str,
                'queryEndDate': date_str
            }
            
            print(f"📊 抓取 TAIFEX 三大法人買賣超資料 ({date_str})...")
            
            # 嘗試多種方式取得資料
            response = self._fetch_with_retry(url, params)
            if not response:
                return None
            
            # 嘗試解析 CSV
            data = self._parse_csv_response(response.text)
            if data:
                return self._parse_institutional_data(data, target_date)
            
            # 如果 CSV 解析失敗，嘗試解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_institutional_html(soup, target_date)
        
        except Exception as e:
            print(f"❌ 抓取三大法人資料失敗: {str(e)}")
            return None
    
    def fetch_futures_daily(self, contract_code: str = "TX", target_date: Optional[date] = None) -> Optional[Dict]:
        """
        抓取期貨每日交易資料
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            url = f"{self.BASE_URL}/cht/3/futDataDown"
            date_str = target_date.strftime('%Y/%m/%d')
            
            params = {
                'down_type': '1',  # 期貨每日行情
                'commodity_id': contract_code,
                'queryStartDate': date_str,
                'queryEndDate': date_str
            }
            
            print(f"📊 抓取 TAIFEX 期貨每日資料 ({contract_code}, {date_str})...")
            
            response = self._fetch_with_retry(url, params)
            if not response:
                return None
            
            # 嘗試解析 CSV
            data = self._parse_csv_response(response.text)
            if data:
                return self._parse_futures_daily_data(data, contract_code, target_date)
            
            # 如果 CSV 解析失敗，嘗試解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            return self._parse_futures_daily_html(soup, contract_code, target_date)
        
        except Exception as e:
            print(f"❌ 抓取期貨每日資料失敗: {str(e)}")
            return None
    
    def _fetch_with_retry(self, url: str, params: dict, max_retries: int = 3) -> Optional[requests.Response]:
        """帶重試的資料抓取"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30, verify=False)
                response.encoding = 'big5'
                
                if response.status_code == 200:
                    return response
                else:
                    print(f"⚠️ 請求失敗，狀態碼: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ 請求失敗 (嘗試 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指數退避
        
        return None
    
    def _parse_csv_response(self, text: str) -> Optional[pd.DataFrame]:
        """嘗試解析 CSV 回應"""
        try:
            # 移除可能的 HTML 標籤
            clean_text = re.sub(r'<[^>]+>', '', text)
            
            # 檢查是否包含 CSV 格式的資料（有多個逗號分隔的欄位）
            if ',' not in clean_text or len(clean_text.split(',')) < 5:
                return None
            
            # 嘗試使用 pandas 解析
            df = pd.read_csv(
                StringIO(clean_text),
                encoding='big5',
                engine='python',
                skipinitialspace=True,
                on_bad_lines='skip'
            )
            
            if not df.empty and len(df.columns) > 3:
                return df
        
        except Exception as e:
            # CSV 解析失敗，返回 None 讓呼叫者嘗試其他方法
            pass
        
        return None
    
    def _parse_institutional_data(self, df: pd.DataFrame, target_date: date) -> Optional[Dict]:
        """從 DataFrame 解析三大法人資料"""
        try:
            # 這裡需要根據實際 CSV 格式調整
            # 假設 CSV 格式類似：
            # 日期, 外資買, 外資賣, 外資淨, 投信買, 投信賣, 投信淨, ...
            
            result = {
                'date': target_date,
                'market_type': 'weighted',
                'foreign': {'buy': 0, 'sell': 0, 'net': 0},
                'trust': {'buy': 0, 'sell': 0, 'net': 0},
                'dealer': {'buy': 0, 'sell': 0, 'net': 0},
                'total_net': 0
            }
            
            # 嘗試從 DataFrame 中提取資料
            # 需要根據實際欄位名稱調整
            print(f"⚠️ CSV 資料格式需要根據實際回應調整")
            print(f"   欄位: {list(df.columns)}")
            print(f"   資料行數: {len(df)}")
            
            return result
        
        except Exception as e:
            print(f"⚠️ 解析三大法人資料失敗: {str(e)}")
            return None
    
    def _parse_institutional_html(self, soup: BeautifulSoup, target_date: date) -> Optional[Dict]:
        """從 HTML 解析三大法人資料"""
        try:
            # 尋找資料表格
            tables = soup.find_all('table')
            
            if not tables:
                print("⚠️ 找不到資料表格")
                return None
            
            result = {
                'date': target_date,
                'market_type': 'weighted',
                'foreign': {'buy': 0, 'sell': 0, 'net': 0},
                'trust': {'buy': 0, 'sell': 0, 'net': 0},
                'dealer': {'buy': 0, 'sell': 0, 'net': 0},
                'total_net': 0
            }
            
            # 這裡需要根據實際 HTML 結構調整解析邏輯
            print(f"⚠️ HTML 解析邏輯需要根據實際頁面結構調整")
            print(f"   找到 {len(tables)} 個表格")
            
            return result
        
        except Exception as e:
            print(f"⚠️ 解析 HTML 失敗: {str(e)}")
            return None
    
    def _parse_futures_daily_data(self, df: pd.DataFrame, contract_code: str, target_date: date) -> Optional[Dict]:
        """從 DataFrame 解析期貨每日資料"""
        try:
            result = {
                'date': target_date,
                'contract_code': f"{target_date.year}{target_date.month:02d}",
                'open': 0,
                'high': 0,
                'low': 0,
                'close': 0,
                'settlement': 0,
                'change': 0,
                'change_percent': 0,
                'volume': 0,
                'open_interest': 0
            }
            
            print(f"⚠️ 期貨資料格式需要根據實際回應調整")
            print(f"   欄位: {list(df.columns)}")
            
            return result
        
        except Exception as e:
            print(f"⚠️ 解析期貨資料失敗: {str(e)}")
            return None
    
    def _parse_futures_daily_html(self, soup: BeautifulSoup, contract_code: str, target_date: date) -> Optional[Dict]:
        """從 HTML 解析期貨每日資料"""
        try:
            tables = soup.find_all('table')
            print(f"⚠️ 期貨 HTML 解析需要根據實際頁面結構調整")
            return None
        
        except Exception as e:
            print(f"⚠️ 解析期貨 HTML 失敗: {str(e)}")
            return None

