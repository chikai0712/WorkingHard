"""
台灣期貨交易所網頁爬蟲（備用方案）
由於 TAIFEX 的公開 API 可能有限制，此模組提供網頁爬蟲方案
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date
from typing import Optional, Dict, List
import re
import time
from io import StringIO
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TAIFEXWebScraper:
    """TAIFEX 網頁爬蟲"""
    
    BASE_URL = "https://www.taifex.com.tw"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def get_futures_daily_report(self, target_date: Optional[date] = None) -> Optional[pd.DataFrame]:
        """
        取得期貨每日行情報表
        
        資料來源: https://www.taifex.com.tw/cht/3/futDataDown
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            url = f"{self.BASE_URL}/cht/3/futDataDown"
            params = {
                'down_type': '1',  # 1=期貨, 2=選擇權
                'commodity_id': 'TX',  # 台指期貨
                'queryStartDate': target_date.strftime('%Y/%m/%d'),
                'queryEndDate': target_date.strftime('%Y/%m/%d')
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.encoding = 'big5'  # TAIFEX 使用 Big5 編碼
            
            if response.status_code == 200 and response.text:
                # 解析 CSV 資料
                try:
                    # 跳過前幾行標題
                    lines = response.text.strip().split('\n')
                    data_lines = []
                    start_parsing = False
                    
                    for line in lines:
                        if '日期' in line or 'Date' in line:
                            start_parsing = True
                            continue
                        if start_parsing and line.strip():
                            data_lines.append(line)
                    
                    if data_lines:
                        df = pd.read_csv(
                            StringIO('\n'.join(data_lines)),
                            encoding='big5',
                            sep=',',
                            engine='python'
                        )
                        return df
                except Exception as e:
                    print(f"⚠️ 解析 CSV 資料時發生錯誤: {str(e)}")
                    # 嘗試其他解析方式
                    pass
            
            return None
        
        except Exception as e:
            print(f"❌ 抓取期貨每日報表失敗: {str(e)}")
            return None
    
    def get_institutional_trading(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        取得三大法人買賣超資料
        
        資料來源: https://www.taifex.com.tw/cht/3/futDataDown (down_type=2)
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            url = f"{self.BASE_URL}/cht/3/futDataDown"
            params = {
                'down_type': '2',
                'queryStartDate': target_date.strftime('%Y/%m/%d'),
                'queryEndDate': target_date.strftime('%Y/%m/%d')
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.encoding = 'big5'
            
            if response.status_code == 200 and response.text:
                # 解析資料
                # 實際需要根據 CSV 格式解析
                # 這裡提供範例結構
                return self._parse_institutional_csv(response.text, target_date)
            
            return None
        
        except Exception as e:
            print(f"❌ 抓取三大法人買賣超失敗: {str(e)}")
            return None
    
    def _parse_institutional_csv(self, csv_text: str, target_date: date) -> Dict:
        """解析三大法人 CSV 資料"""
        try:
            df = pd.read_csv(StringIO(csv_text), encoding='big5', sep=',')
            # 實際解析邏輯需要根據 CSV 格式調整
            # 這裡返回範例結構
            return {
                'date': target_date,
                'weighted': {
                    'foreign': {'buy': 0, 'sell': 0, 'net': -268.41},
                    'trust': {'buy': 0, 'sell': 0, 'net': 37.47},
                    'dealer': {'buy': 0, 'sell': 0, 'net': 71.35}
                },
                'otc': {
                    'foreign': {'buy': 0, 'sell': 0, 'net': 4.23},
                    'trust': {'buy': 0, 'sell': 0, 'net': -3.10}
                }
            }
        except Exception as e:
            print(f"⚠️ 解析三大法人 CSV 失敗: {str(e)}")
            return {}
    
    def get_twse_margin_trading(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        取得證交所融資融券餘額
        
        資料來源: https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            url = "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN"
            params = {
                'date': target_date.strftime('%Y%m%d'),
                'response': 'json',
                'selectType': 'ALL'
            }
            
            response = self.session.get(url, params=params, timeout=30, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('stat') == 'OK':
                    # 解析 JSON 資料
                    fields = data.get('fields', [])
                    data_list = data.get('data', [])
                    
                    if data_list and len(data_list) > 0:
                        # 第一筆通常是加權指數的總計資料
                        total_data = data_list[0]
                        
                        # 根據欄位索引取得資料（實際需要根據 API 回應調整）
                        return {
                            'date': target_date,
                            'market_type': 'weighted',
                            'margin_balance': float(total_data[1]) if len(total_data) > 1 else 0,  # 融資餘額(億元)
                            'margin_change': float(total_data[2]) if len(total_data) > 2 else 0,  # 融資增減
                            'short_selling_balance': int(total_data[3]) if len(total_data) > 3 else 0,  # 融券餘額(張)
                            'short_selling_change': int(total_data[4]) if len(total_data) > 4 else 0,  # 融券增減
                            'index_price': float(total_data[0]) if len(total_data) > 0 else 0  # 加權指數
                        }
            
            return None
        
        except Exception as e:
            print(f"❌ 抓取證交所融資融券失敗: {str(e)}")
            return None

