"""
HiStock (嗨投資) 資料爬蟲
作為 TAIFEX/TWSE 的備用資料來源
"""

import requests
from bs4 import BeautifulSoup
from datetime import date
from typing import Optional, Dict
from sqlalchemy.orm import Session
import time
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HiStockScraper:
    """HiStock (嗨投資) 資料爬蟲"""
    
    BASE_URL = "https://histock.tw"
    
    def __init__(self, db: Session):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        })
    
    def fetch_institutional_trading(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        抓取三大法人買賣超資料
        
        可能的路徑：
        - https://histock.tw/stock/major.aspx
        - https://histock.tw/台股大盤/三大法人
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # 嘗試訪問三大法人頁面
            urls_to_try = [
                f"{self.BASE_URL}/stock/three.aspx",  # 三大法人專門頁面
                f"{self.BASE_URL}/stock/major.aspx",
                f"{self.BASE_URL}/stock/major",
                f"{self.BASE_URL}/台股大盤",  # 台股大盤頁面也包含三大法人資料
            ]
            
            print(f"📊 從 HiStock 抓取三大法人資料 ({target_date.strftime('%Y-%m-%d')})...")
            
            for url in urls_to_try:
                try:
                    response = self.session.get(url, timeout=30, verify=False)
                    response.encoding = 'utf-8'
                    
                    if response.status_code == 200 and ('三大法人' in response.text or '外資' in response.text):
                        soup = BeautifulSoup(response.text, 'html.parser')
                        data = self._parse_institutional_table(soup, target_date)
                        
                        if data:
                            print(f"✅ 成功從 HiStock 取得三大法人資料")
                            return data
                        
                except Exception as e:
                    continue
            
            print(f"⚠️ 無法從 HiStock 取得三大法人資料")
            return None
        
        except Exception as e:
            print(f"❌ 從 HiStock 抓取三大法人資料失敗: {str(e)}")
            return None
    
    def fetch_margin_trading(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        抓取融資融券資料
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            urls_to_try = [
                f"{self.BASE_URL}/stock/margin.aspx",
                f"{self.BASE_URL}/stock/margin",
                f"{self.BASE_URL}/台股大盤/融資融券",
            ]
            
            print(f"📊 從 HiStock 抓取融資融券資料 ({target_date.strftime('%Y-%m-%d')})...")
            
            for url in urls_to_try:
                try:
                    response = self.session.get(url, timeout=30, verify=False)
                    response.encoding = 'utf-8'
                    
                    if response.status_code == 200 and ('融資' in response.text or '融券' in response.text):
                        soup = BeautifulSoup(response.text, 'html.parser')
                        data = self._parse_margin_table(soup, target_date)
                        
                        if data:
                            print(f"✅ 成功從 HiStock 取得融資融券資料")
                            return data
                
                except Exception as e:
                    continue
            
            print(f"⚠️ 無法從 HiStock 取得融資融券資料")
            return None
        
        except Exception as e:
            print(f"❌ 從 HiStock 抓取融資融券資料失敗: {str(e)}")
            return None
    
    def _parse_institutional_table(self, soup: BeautifulSoup, target_date: date) -> Optional[Dict]:
        """從 HTML 表格解析三大法人資料"""
        try:
            result = {
                'date': target_date,
                'market_type': 'weighted',
                'foreign': {'buy': 0, 'sell': 0, 'net': 0},
                'trust': {'buy': 0, 'sell': 0, 'net': 0},
                'dealer': {'buy': 0, 'sell': 0, 'net': 0},
                'total_net': 0
            }
            
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                table_text = table.get_text()
                
                # 檢查是否包含三大法人相關資料
                if '外資' not in table_text and '投信' not in table_text:
                    continue
                
                # 尋找表頭
                header_row = None
                header_row_idx = None
                for idx, row in enumerate(rows):
                    headers = [th.get_text(strip=True) for th in row.find_all(['th', 'td'])]
                    headers_text = ' '.join(headers)
                    
                    # HiStock 的表頭格式：['日期', '外資', '投信', '自營(總)', ...]
                    # 應該包含「日期」和「外資」或「投信」等關鍵字
                    if ('日期' in headers_text and ('外資' in headers_text or '投信' in headers_text)) and len(headers) >= 3:
                        header_row = headers
                        header_row_idx = idx
                        break
                
                if not header_row:
                    continue
                
                # HiStock 的表格結構是：
                # 表頭: ['日期', '外資', '投信', '自營(總)', '自營自買', '自營避險', '總計']
                # 資料行: ['12/19', '-1.97', '44.99', '75.39', '44.27', '31.13', '118.41']
                # 第一行資料就是最新日期（通常是今天或昨天）
                
                # 解析資料行（從第一行開始，因為第一行就是最新資料）
                for row_idx in range(header_row_idx + 1, min(header_row_idx + 6, len(rows))):  # 只檢查前5行
                    row = rows[row_idx]
                    cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                    
                    if not cells or len(cells) < 4:
                        continue
                    
                    first_cell = cells[0] if cells else ''
                    
                    # 檢查第一列是否是日期格式（MM/DD 或 YYYY/MM/DD）
                    is_date_row = False
                    if '/' in first_cell:
                        date_parts = first_cell.split('/')
                        if len(date_parts) >= 2 and date_parts[0].isdigit() and date_parts[1].isdigit():
                            is_date_row = True
                    
                    if is_date_row:
                        # 這是日期行，根據表頭位置提取各法人的數值
                        row_date_str = first_cell  # 例如: "12/19"
                        
                        # 檢查這一行是否是指定日期的資料
                        # HiStock 的日期格式是 MM/DD，需要轉換
                        target_month = target_date.month
                        target_day = target_date.day
                        
                        # 解析行中的日期
                        row_month = None
                        row_day = None
                        if '/' in row_date_str:
                            parts = row_date_str.split('/')
                            if len(parts) >= 2:
                                try:
                                    row_month = int(parts[0])
                                    row_day = int(parts[1])
                                except:
                                    pass
                        
                        # 如果日期匹配，或者這是第一行資料（最新日期），就使用它
                        use_this_row = False
                        if row_month == target_month and row_day == target_day:
                            use_this_row = True
                            print(f"      ✅ 找到指定日期 ({target_date.strftime('%Y-%m-%d')}) 的資料")
                        elif row_idx == header_row_idx + 1 and target_date == date.today():
                            # 如果是今天且是第一行資料，也可以使用
                            use_this_row = True
                            print(f"      ✅ 使用最新資料（日期: {row_date_str}）")
                        
                        if use_this_row:
                            for h_idx, header in enumerate(header_row):
                                if h_idx >= len(cells):
                                    break
                                
                                header_text = header.lower()
                                
                                # 外資
                                if '外資' in header and '總' not in header:
                                    result['foreign']['net'] = self._safe_float(cells, h_idx)
                                
                                # 投信
                                elif '投信' in header:
                                    result['trust']['net'] = self._safe_float(cells, h_idx)
                                
                                # 自營(總)
                                elif '自營' in header and '總' in header:
                                    result['dealer']['net'] = self._safe_float(cells, h_idx)
                                
                                # 自營自買
                                elif '自營' in header and '自買' in header:
                                    result['dealer']['self_buy'] = self._safe_float(cells, h_idx)
                                    result['dealer']['self_net'] = self._safe_float(cells, h_idx)
                                
                                # 自營避險
                                elif '自營' in header and '避險' in header:
                                    result['dealer']['hedge_net'] = self._safe_float(cells, h_idx)
                                
                                # 總計
                                elif '總計' in header or '合計' in header:
                                    result['total_net'] = self._safe_float(cells, h_idx)
                            
                            # 解析成功，顯示結果
                            if result['foreign']['net'] != 0 or result['trust']['net'] != 0 or result['dealer']['net'] != 0:
                                print(f"      ✅ 解析 HiStock 三大法人資料（日期: {row_date_str}）")
                                print(f"         外資: {result['foreign']['net']:.2f}億")
                                print(f"         投信: {result['trust']['net']:.2f}億")
                                print(f"         自營: {result['dealer']['net']:.2f}億")
                                break  # 找到資料後就停止
                
                # 如果成功解析到資料
                if result['foreign']['net'] != 0 or result['trust']['net'] != 0 or result['dealer']['net'] != 0:
                    result['total_net'] = result['foreign']['net'] + result['trust']['net'] + result['dealer']['net']
                    return result
            
            return None
        
        except Exception as e:
            print(f"⚠️ 解析 HiStock 三大法人表格失敗: {str(e)}")
            return None
    
    def _parse_margin_table(self, soup: BeautifulSoup, target_date: date) -> Optional[Dict]:
        """從 HTML 表格解析融資融券資料"""
        try:
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
            
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                table_text = table.get_text()
                
                if '融資' not in table_text and '融券' not in table_text:
                    continue
                
                # 解析邏輯類似 _parse_institutional_table
                # 這裡先返回空結構，待實際頁面結構確認後再實現
                print(f"⚠️ HiStock 融資融券解析邏輯待實現")
                return None
            
            return None
        
        except Exception as e:
            print(f"⚠️ 解析 HiStock 融資融券表格失敗: {str(e)}")
            return None
    
    def _parse_financial_row(self, cells: list, headers: list) -> Dict:
        """解析法人資料行"""
        result = {'buy': 0, 'sell': 0, 'net': 0}
        
        try:
            # 根據表頭找到對應欄位
            buy_idx = None
            sell_idx = None
            net_idx = None
            
            for i, header in enumerate(headers):
                header_lower = header.lower()
                if '買進' in header or 'buy' in header_lower or ('買' in header and '賣' not in header):
                    buy_idx = i
                elif '賣出' in header or 'sell' in header_lower or ('賣' in header and '買' not in header):
                    sell_idx = i
                elif '買賣超' in header or 'net' in header_lower or '淨' in header:
                    net_idx = i
            
            # 提取數值
            if buy_idx is not None and buy_idx < len(cells):
                result['buy'] = self._safe_float(cells, buy_idx)
            if sell_idx is not None and sell_idx < len(cells):
                result['sell'] = self._safe_float(cells, sell_idx)
            if net_idx is not None and net_idx < len(cells):
                result['net'] = self._safe_float(cells, net_idx)
            elif buy_idx is not None and sell_idx is not None:
                # 如果沒有淨值欄位，計算差值
                result['net'] = result['buy'] - result['sell']
        
        except Exception as e:
            pass
        
        return result
    
    def _safe_float(self, cells: list, index: int) -> float:
        """安全地從列表取得浮點數（億元單位）"""
        try:
            if index is None or index >= len(cells) or index < 0:
                return 0.0
            
            value = cells[index].replace(',', '').strip()
            # 移除可能的單位（億、萬元等）
            if '億' in value:
                value = value.replace('億', '')
                multiplier = 1.0
            elif '萬' in value:
                value = value.replace('萬', '')
                multiplier = 0.0001  # 轉換為億元
            else:
                multiplier = 1.0
            
            try:
                return float(value) * multiplier
            except:
                return 0.0
        except:
            return 0.0

