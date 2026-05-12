"""
TWSE 即時行情 API（約 20 秒延遲）
整合台灣證券交易所的即時交易資料
"""

import requests
from datetime import datetime, date
from typing import Optional, Dict, List
import json
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TWSERealtimeClient:
    """TWSE 即時行情 API 客戶端（約 20 秒延遲）"""
    
    BASE_URL = "https://www.twse.com.tw/rwd/zh"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
        })
    
    def get_stock_realtime(self, symbol: str) -> Optional[Dict]:
        """
        取得單一股票的即時行情（約 20 秒延遲）
        
        Args:
            symbol: 股票代號（如 '2330'）
        
        Returns:
            包含即時行情的字典，失敗返回 None
        """
        try:
            # TWSE 個股即時資訊 API
            url = f"{self.BASE_URL}/realtimeTrading/STOCK_DAY"
            
            # 使用今天的日期
            today = date.today()
            date_str = today.strftime('%Y%m%d')
            
            params = {
                'response': 'json',
                'date': date_str,
                'stockNo': symbol
            }
            
            response = self.session.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if data.get('stat') == 'OK':
                return self._parse_realtime_data(data, symbol)
            else:
                print(f"⚠️ API 回應錯誤: {data.get('stat')}")
                return None
        
        except Exception as e:
            print(f"❌ 取得 {symbol} 即時行情失敗: {str(e)}")
            return None
    
    def get_multiple_stocks_realtime(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """
        取得多檔股票的即時行情
        
        Args:
            symbols: 股票代號列表
        
        Returns:
            字典，key 為股票代號，value 為行情資料
        """
        results = {}
        
        for symbol in symbols:
            data = self.get_stock_realtime(symbol)
            results[symbol] = data
            
            # 避免請求過快（TWSE 有速率限制）
            time.sleep(0.5)
        
        return results
    
    def get_stock_day(self, symbol: str, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        取得股票的每日收盤行情
        
        Args:
            symbol: 股票代號
            target_date: 目標日期（預設為今天）
        
        Returns:
            包含每日行情的字典
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            date_str = target_date.strftime('%Y%m%d')
            url = f"{self.BASE_URL}/afterTrading/STOCK_DAY"
            
            params = {
                'response': 'json',
                'date': date_str,
                'stockNo': symbol
            }
            
            response = self.session.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()
            
            if data.get('stat') == 'OK':
                return self._parse_day_data(data, symbol, target_date)
            else:
                print(f"⚠️ API 回應錯誤: {data.get('stat')}")
                return None
        
        except Exception as e:
            print(f"❌ 取得 {symbol} 每日行情失敗: {str(e)}")
            return None
    
    def _parse_realtime_data(self, data: Dict, symbol: str) -> Optional[Dict]:
        """解析即時行情資料"""
        try:
            fields = data.get('fields', [])
            data_list = data.get('data', [])
            
            if not data_list or len(data_list) == 0:
                return None
            
            # 取得最新的資料（第一筆）
            latest = data_list[0] if data_list else []
            
            # 建立欄位映射
            field_map = {field: i for i, field in enumerate(fields)}
            
            result = {
                'symbol': symbol,
                'date': date.today(),
                'timestamp': datetime.now(),
                'open': self._safe_get(latest, field_map.get('開盤價', 1)),
                'high': self._safe_get(latest, field_map.get('最高價', 2)),
                'low': self._safe_get(latest, field_map.get('最低價', 3)),
                'close': self._safe_get(latest, field_map.get('收盤價', 4)),
                'volume': self._safe_get(latest, field_map.get('成交股數', 5), is_int=True),
                'turnover': self._safe_get(latest, field_map.get('成交金額', 6)),
                'change': self._safe_get(latest, field_map.get('漲跌價差', 7)),
                'change_percent': self._safe_get(latest, field_map.get('漲跌幅', 8)),
                'transaction_count': self._safe_get(latest, field_map.get('成交筆數', 9), is_int=True),
            }
            
            return result
        
        except Exception as e:
            print(f"❌ 解析即時行情資料失敗: {str(e)}")
            return None
    
    def _parse_day_data(self, data: Dict, symbol: str, target_date: date) -> Optional[Dict]:
        """解析每日行情資料"""
        try:
            fields = data.get('fields', [])
            data_list = data.get('data', [])
            
            if not data_list or len(data_list) == 0:
                return None
            
            # 取得最新的資料（最後一筆通常是當天的資料）
            latest = data_list[-1] if data_list else []
            
            # 建立欄位映射
            field_map = {field: i for i, field in enumerate(fields)}
            
            result = {
                'symbol': symbol,
                'date': target_date,
                'open': self._safe_get(latest, field_map.get('開盤價', 1)),
                'high': self._safe_get(latest, field_map.get('最高價', 2)),
                'low': self._safe_get(latest, field_map.get('最低價', 3)),
                'close': self._safe_get(latest, field_map.get('收盤價', 4)),
                'volume': self._safe_get(latest, field_map.get('成交股數', 5), is_int=True),
                'turnover': self._safe_get(latest, field_map.get('成交金額', 6)),
                'change': self._safe_get(latest, field_map.get('漲跌價差', 7)),
                'change_percent': self._safe_get(latest, field_map.get('漲跌幅', 8)),
            }
            
            return result
        
        except Exception as e:
            print(f"❌ 解析每日行情資料失敗: {str(e)}")
            return None
    
    def _safe_get(self, row: list, index: Optional[int], default=0, is_int=False):
        """安全地從列表中取得值"""
        try:
            if index is None or index >= len(row):
                return default
            
            value = row[index]
            
            if isinstance(value, str):
                # 移除千分位逗號和其他符號
                value = value.replace(',', '').replace('--', '').strip()
                
                if not value or value == '':
                    return default
                
                try:
                    if is_int:
                        return int(float(value))
                    return float(value)
                except:
                    return default
            
            if value is None:
                return default
            
            if is_int:
                return int(float(value))
            return float(value)
        
        except Exception as e:
            return default

