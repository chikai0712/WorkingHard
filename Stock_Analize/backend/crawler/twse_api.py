"""
台灣證券交易所 API 封裝
"""

import requests
from datetime import date
from typing import Optional, Dict
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TWSEClient:
    """台灣證券交易所 API 客戶端"""
    
    BASE_URL = "https://www.twse.com.tw/rwd/zh"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_margin_trading(self, target_date: date) -> Optional[Dict]:
        """
        取得融資融券餘額資料
        
        API: https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN
        """
        url = f"{self.BASE_URL}/marginTrading/MI_MARGN"
        date_str = target_date.strftime('%Y%m%d')
        
        params = {
            'date': date_str,
            'response': 'json',
            'selectType': 'ALL'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if data.get('stat') == 'OK':
                fields = data.get('fields', [])
                data_list = data.get('data', [])
                
                # 根據實際 API 回應結構解析
                # API 回應有 tables 陣列，每個 table 有不同的資料
                tables = data.get('tables', [])
                
                if not tables:
                    print(f"⚠️ API 回應沒有 tables (可能非交易日): {date_str}")
                    return None
                
                result = {
                    'date': target_date,
                    'market_type': 'weighted',
                    'margin_balance': 0,
                    'margin_change': 0,
                    'short_selling_balance': 0,
                    'short_selling_change': 0,
                    'securities_lending_sell': 0,
                    'securities_lending_change': 0,
                    'index_price': 0,
                    'index_change_percent': 0
                }
                
                # 解析第一個 table（信用交易統計）
                if len(tables) > 0:
                    table = tables[0]
                    table_fields = table.get('fields', [])
                    table_data = table.get('data', [])
                    
                    # 找出欄位索引
                    field_map = {field: i for i, field in enumerate(table_fields)}
                    
                    # 解析融資資料
                    for row in table_data:
                        if len(row) > 0:
                            item_name = str(row[0])
                            
                            # 融資金額(仟元) - 今日餘額
                            if '融資金額' in item_name:
                                if '今日餘額' in field_map:
                                    idx = field_map['今日餘額']
                                    if idx < len(row):
                                        # 轉換為億元（仟元 * 1000 / 100000000）
                                        result['margin_balance'] = self._safe_get(row, idx) * 1000 / 100000000
                                
                                if '前日餘額' in field_map and '今日餘額' in field_map:
                                    today_idx = field_map['今日餘額']
                                    prev_idx = field_map['前日餘額']
                                    result['margin_change'] = (self._safe_get(row, today_idx) - self._safe_get(row, prev_idx)) * 1000 / 100000000
                            
                            # 融券(交易單位) - 今日餘額（張）
                            elif '融券(交易單位)' in item_name:
                                if '今日餘額' in field_map:
                                    idx = field_map['今日餘額']
                                    result['short_selling_balance'] = self._safe_get(row, idx)
                                
                                if '前日餘額' in field_map and '今日餘額' in field_map:
                                    today_idx = field_map['今日餘額']
                                    prev_idx = field_map['前日餘額']
                                    result['short_selling_change'] = self._safe_get(row, today_idx) - self._safe_get(row, prev_idx)
                
                return result
            
            return None
        
        except Exception as e:
            print(f"❌ 取得融資融券資料失敗: {str(e)}")
            return None
    
    def _safe_get(self, row: list, index: int, default=0):
        """安全地從列表中取得值"""
        try:
            if index is None or index >= len(row):
                return default
            value = row[index]
            if isinstance(value, str):
                # 移除千分位逗號
                value = value.replace(',', '')
                try:
                    return float(value)
                except:
                    return default
            return float(value) if value else default
        except:
            return default

