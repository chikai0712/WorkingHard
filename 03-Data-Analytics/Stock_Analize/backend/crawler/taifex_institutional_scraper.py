"""
TAIFEX 三大法人資料爬蟲
使用網頁爬蟲方式取得三大法人買賣超資料
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date
from typing import Optional, Dict
from sqlalchemy.orm import Session
import time
import re
from io import StringIO
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TAIFEXInstitutionalScraper:
    """TAIFEX 三大法人資料爬蟲"""
    
    BASE_URL = "https://www.taifex.com.tw"
    
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
        
        先嘗試訪問資料頁面，從 HTML 表格中提取資料
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # 方法1: 嘗試直接訪問資料頁面
            url = f"{self.BASE_URL}/cht/3/futContractsDate"
            params = {
                'queryDate': target_date.strftime('%Y/%m/%d')
            }
            
            print(f"📊 抓取 TAIFEX 三大法人買賣超資料 ({target_date.strftime('%Y/%m/%d')})...")
            
            response = self.session.get(url, params=params, timeout=30, verify=False)
            
            # 嘗試自動檢測編碼
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                # 嘗試常見的繁體中文編碼
                for encoding in ['big5', 'cp950', 'utf-8', 'big5hkscs']:
                    try:
                        response.encoding = encoding
                        test_text = response.text[:500]
                        if '外資' in test_text or '投信' in test_text or '自營' in test_text:
                            break
                    except:
                        continue
            
            if not response.encoding:
                response.encoding = 'big5'
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 尋找資料表格
                data = self._parse_institutional_table(soup, target_date)
                if data:
                    return data
                
                # 如果找不到表格，嘗試尋找 CSV 下載連結
                csv_data = self._try_download_csv(soup, target_date)
                if csv_data:
                    return csv_data
            
            print(f"⚠️ 無法取得三大法人資料")
            return None
        
        except Exception as e:
            print(f"❌ 抓取三大法人資料失敗: {str(e)}")
            return None
    
    def _parse_institutional_table(self, soup: BeautifulSoup, target_date: date) -> Optional[Dict]:
        """從 HTML 表格解析三大法人資料"""
        try:
            tables = soup.find_all('table')
            
            if not tables:
                return None
            
            result = {
                'date': target_date,
                'market_type': 'weighted',
                'foreign': {'buy': 0, 'sell': 0, 'net': 0},
                'trust': {'buy': 0, 'sell': 0, 'net': 0},
                'dealer': {'buy': 0, 'sell': 0, 'net': 0, 'self_buy': 0, 'self_sell': 0, 'self_net': 0, 'hedge_buy': 0, 'hedge_sell': 0, 'hedge_net': 0},
                'total_net': 0
            }
            
            # 遍歷所有表格，尋找包含三大法人資料的表格
            for table_idx, table in enumerate(tables):
                rows = table.find_all('tr')
                
                if len(rows) < 3:
                    continue
                
                # 先取得表格的所有文字，檢查是否包含關鍵字
                table_text = table.get_text()
                if '外資' not in table_text and '投信' not in table_text and '自營' not in table_text:
                    continue
                
                # 尋找表頭行
                # TAIFEX 表格結構：
                # 行 0: ['', '交易口數與契約金額', '未平倉餘額']
                # 行 1: ['多方', '空方', '多空淨額', ...]
                # 行 2: ['序號', '商品名稱', '身份別', '口數', '契約金額', '口數', '契約金額', ...]
                # 行 3+: 資料行
                header_row = None
                header_row_idx = None
                for idx, row in enumerate(rows):
                    headers = [th.get_text(strip=True) for th in row.find_all(['th', 'td'])]
                    if not headers or len(headers) < 5:
                        continue
                    
                    headers_text = ' '.join(headers)
                    first_cell = headers[0] if headers else ''
                    
                    # 表頭應該包含「序號」或「商品名稱」或「身份別」，且第一個單元格不應該是數字
                    if ('序號' in headers_text or '商品名稱' in headers_text or '身份別' in headers_text) and not first_cell.isdigit():
                        header_row = headers
                        header_row_idx = idx
                        break
                
                if not header_row:
                    continue
                
                print(f"   找到表頭（表格 {table_idx+1}，行 {header_row_idx+1}）: {header_row[:6]}")
                
                # 從表頭行之後開始解析資料行
                # 注意：這個表格的結構是：
                # 欄位 0: 序號
                # 欄位 1: 商品名稱
                # 欄位 2: 身份別
                # 欄位 3-5: 交易口數（多方、空方、多空淨額）
                # 欄位 6-8: 契約金額（多方、空方、多空淨額）- 這是我們需要的買賣超金額！
                # 欄位 9-11: 未平倉餘額（多方、空方、多空淨額）
                
                # 先找到臺股期貨的商品行
                tx_futures_row_idx = None
                for row_idx in range(header_row_idx + 1, len(rows)):
                    row = rows[row_idx]
                    cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                    
                    if len(cells) >= 2:
                        commodity = cells[1] if len(cells) > 1 else ''
                        if '臺股期貨' in commodity or '台股期貨' in commodity:
                            tx_futures_row_idx = row_idx
                            break
                
                if tx_futures_row_idx is None:
                    continue
                
                # 從臺股期貨行開始，檢查後續的法人資料行
                # 外資、投信、自營商通常緊跟在臺股期貨行之後
                # 注意：外資和投信的行結構不同：
                #   - 自營商：欄位 0=序號, 欄位 1=商品名稱, 欄位 2=身份別（15欄位）
                #   - 外資/投信：欄位 0=身份別, 欄位 1=口數, 欄位 2=契約金額（13欄位）
                for row_idx in range(tx_futures_row_idx, min(tx_futures_row_idx + 5, len(rows))):
                    row = rows[row_idx]
                    cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                    
                    if not cells or len(cells) < 9:
                        continue
                    
                    # 檢查欄位結構
                    # 情況1: 自營商格式（15欄位）- 欄位 0=序號, 欄位 1=商品名稱, 欄位 2=身份別
                    # 情況2: 外資/投信格式（13欄位）- 欄位 0=身份別, 欄位 1=口數, 欄位 2=契約金額
                    
                    identity = ''
                    commodity = ''
                    buy_amount = 0
                    sell_amount = 0
                    net_amount = 0
                    is_tx_related = False
                    
                    # 檢查是否是自營商格式（15欄位）
                    if len(cells) >= 15:
                        commodity = cells[1] if len(cells) > 1 else ''
                        identity = cells[2] if len(cells) > 2 else ''
                        
                        if ('臺股期貨' in commodity or '台股期貨' in commodity) and identity == '自營商':
                            is_tx_related = True
                            # 欄位 6: 多方契約金額（買進）
                            # 欄位 7: 空方契約金額（賣出）
                            # 欄位 8: 多空淨額契約金額（淨買賣超）
                            buy_amount = self._safe_float(cells, 6) / 100000000
                            sell_amount = self._safe_float(cells, 7) / 100000000
                            net_amount = self._safe_float(cells, 8) / 100000000
                            
                            # 根據 TAIFEX 網頁實際結構，15欄位的格式應該是：
                            # 欄位 9: 多方未平倉口數
                            # 欄位 10: 多方未平倉契約金額
                            # 欄位 11: 空方未平倉口數
                            # 欄位 12: 空方未平倉契約金額
                            # 欄位 13: 多空淨額未平倉口數（這才是我們要的！）
                            # 欄位 14: 多空淨額未平倉契約金額
                            if len(cells) >= 14:
                                oi_long = self._safe_int(cells, 9)  # 多方未平倉口數
                                oi_short = self._safe_int(cells, 11)  # 空方未平倉口數
                                oi_net = self._safe_int(cells, 13)  # 多空淨額未平倉口數
                                # 儲存到 result 中供後續使用
                                if 'open_interest' not in result:
                                    result['open_interest'] = {}
                                result['open_interest']['dealer_oi'] = oi_net
                                print(f"      ✅ 解析自營未平倉: {oi_net:,} 口 (多方: {oi_long:,}, 空方: {oi_short:,})")
                    
                    # 檢查是否是外資/投信格式（13欄位）
                    elif len(cells) >= 13:
                        identity = cells[0] if len(cells) > 0 else ''
                        
                        # 確認前幾行（最多3行）是否有臺股期貨
                        # 外資和投信可能在臺股期貨行之後，中間可能有其他法人行
                        if row_idx > tx_futures_row_idx and identity in ['外資', '投信']:
                            # 檢查前3行是否有臺股期貨
                            for check_idx in range(max(header_row_idx + 1, row_idx - 3), row_idx):
                                check_row = rows[check_idx]
                                check_cells = [td.get_text(strip=True) for td in check_row.find_all(['td', 'th'])]
                                if len(check_cells) > 1:
                                    check_commodity = check_cells[1]
                                    if '臺股期貨' in check_commodity or '台股期貨' in check_commodity:
                                        is_tx_related = True
                                        # 外資/投信格式的欄位結構：
                                        # 欄位 0: 身份別
                                        # 欄位 1: 多方口數
                                        # 欄位 2: 多方契約金額（買進）
                                        # 欄位 3: 空方口數
                                        # 欄位 4: 空方契約金額（賣出）
                                        # 欄位 5: 多空淨額口數
                                        # 欄位 6: 多空淨額契約金額（淨額）
                                        # 欄位 7-12: 未平倉相關資料
                                        
                                        # 買進 = 多方契約金額（欄位 2）
                                        # 賣出 = 空方契約金額（欄位 4）
                                        # 淨額 = 多空淨額契約金額（欄位 6）
                                        buy_amount = self._safe_float(cells, 2) / 100000000
                                        sell_amount = self._safe_float(cells, 4) / 100000000
                                        net_amount = self._safe_float(cells, 6) / 100000000
                                        
                                        # 根據 TAIFEX 網頁實際結構（從調試輸出確認），13欄位的格式是：
                                        # 欄位 0: 身份別
                                        # 欄位 1: 多方口數（交易）
                                        # 欄位 2: 多方契約金額（交易）
                                        # 欄位 3: 空方口數（交易）
                                        # 欄位 4: 空方契約金額（交易）
                                        # 欄位 5: 多空淨額口數（交易）
                                        # 欄位 6: 多空淨額契約金額（交易）
                                        # 欄位 7: 多方未平倉口數
                                        # 欄位 8: 多方未平倉契約金額（數值很大，不是口數）
                                        # 欄位 9: 空方未平倉口數
                                        # 欄位 10: 空方未平倉契約金額（數值很大，不是口數）
                                        # 欄位 11: 多空淨額未平倉口數（這才是我們要的！）
                                        # 欄位 12: 多空淨額未平倉契約金額
                                        
                                        if len(cells) >= 12:
                                            # 從欄位 11 提取多空淨額未平倉口數（正確的欄位）
                                            oi_net = self._safe_int(cells, 11) if len(cells) > 11 else 0
                                            oi_long = self._safe_int(cells, 7) if len(cells) > 7 else 0  # 多方未平倉口數
                                            oi_short = self._safe_int(cells, 9) if len(cells) > 9 else 0  # 空方未平倉口數
                                            
                                            # 儲存到 result 中供後續使用
                                            if 'open_interest' not in result:
                                                result['open_interest'] = {}
                                            if '外資' in identity:
                                                result['open_interest']['foreign_oi'] = oi_net
                                                print(f"      ✅ 解析外資未平倉: {oi_net:,} 口 (多方: {oi_long:,}, 空方: {oi_short:,})")
                                            elif '投信' in identity:
                                                result['open_interest']['trust_oi'] = oi_net
                                                print(f"      ✅ 解析投信未平倉: {oi_net:,} 口 (多方: {oi_long:,}, 空方: {oi_short:,})")
                                        break
                    
                    if not is_tx_related:
                        # 如果遇到其他商品，停止搜尋
                        if len(cells) > 1:
                            check_commodity = cells[1]
                            if check_commodity and check_commodity.strip() != '' and '臺股期貨' not in check_commodity and '台股期貨' not in check_commodity:
                                # 檢查序號欄位，如果是新的序號（數字），表示是新的商品
                                if len(cells) > 0 and cells[0].strip().isdigit():
                                    break
                        continue
                    
                    # 外資
                    if '外資' in identity:
                        result['foreign'] = {
                            'buy': buy_amount,
                            'sell': sell_amount,
                            'net': net_amount
                        }
                        print(f"      ✅ 解析外資: 買={buy_amount:.2f}億, 賣={sell_amount:.2f}億, 淨={net_amount:.2f}億")
                    
                    # 投信
                    elif '投信' in identity:
                        result['trust'] = {
                            'buy': buy_amount,
                            'sell': sell_amount,
                            'net': net_amount
                        }
                        print(f"      ✅ 解析投信: 買={buy_amount:.2f}億, 賣={sell_amount:.2f}億, 淨={net_amount:.2f}億")
                    
                    # 自營商（總）
                    elif '自營' in identity:
                        result['dealer'].update({
                            'buy': buy_amount,
                            'sell': sell_amount,
                            'net': net_amount
                        })
                        print(f"      ✅ 解析自營(總): 買={buy_amount:.2f}億, 賣={sell_amount:.2f}億, 淨={net_amount:.2f}億")
                
                # 如果已經成功解析到所有三大法人資料，可以提前結束
                if result['foreign']['net'] != 0 and result['trust']['net'] != 0 and result['dealer']['net'] != 0:
                    break
            
            # 計算總計
            if result['foreign']['net'] != 0 or result['trust']['net'] != 0 or result['dealer']['net'] != 0:
                result['total_net'] = result['foreign']['net'] + result['trust']['net'] + result['dealer']['net']
                print(f"      ✅ 計算總計: {result['total_net']:.2f}億")
            
            # 如果成功解析到資料
            if result['foreign']['net'] != 0 or result['trust']['net'] != 0 or result['dealer']['net'] != 0:
                # 如果有未平倉量資料，也一起返回
                if 'open_interest' in result and result['open_interest']:
                    print(f"      ✅ 同時取得未平倉量資料")
                return result
            
            return None
        
        except Exception as e:
            print(f"⚠️ 解析 HTML 表格失敗: {str(e)}")
            return None
    
    def _parse_financial_row(self, cells: list, headers: list) -> Dict:
        """解析法人資料行"""
        result = {'buy': 0, 'sell': 0, 'net': 0}
        
        # 根據表頭找到對應欄位
        try:
            for i, header in enumerate(headers):
                if i >= len(cells):
                    break
                
                header_lower = header.lower()
                cell_value = self._safe_float(cells, i)
                
                if '買' in header or 'buy' in header_lower:
                    result['buy'] = cell_value
                elif '賣' in header or 'sell' in header_lower:
                    result['sell'] = cell_value
                elif '淨' in header or 'net' in header_lower or '差額' in header:
                    result['net'] = cell_value
        except:
            # 如果無法根據表頭解析，嘗試根據位置推斷
            if len(cells) >= 3:
                result['buy'] = self._safe_float(cells, 1)
                result['sell'] = self._safe_float(cells, 2)
                result['net'] = self._safe_float(cells, 3) if len(cells) > 3 else (result['buy'] - result['sell'])
        
        return result
    
    def _safe_float(self, cells: list, index: int) -> float:
        """安全地從列表取得浮點數"""
        try:
            if index < 0:
                index = len(cells) + index
            
            if index >= len(cells) or index < 0:
                return 0.0
            
            value = cells[index].replace(',', '').strip()
            # 移除可能的單位（億、萬元等）
            value = re.sub(r'[億萬元]', '', value)
            
            try:
                return float(value)
            except:
                return 0.0
        except:
            return 0.0
    
    def _safe_int(self, cells: list, index: int) -> int:
        """安全地從列表取得整數"""
        try:
            if index < 0:
                index = len(cells) + index
            
            if index >= len(cells) or index < 0:
                return 0
            
            value = cells[index].replace(',', '').strip()
            # 移除可能的單位
            value = re.sub(r'[億萬元口張]', '', value)
            
            try:
                return int(float(value))  # 先轉 float 再轉 int，以處理小數點
            except:
                return 0
        except:
            return 0
    
    def _try_download_csv(self, soup: BeautifulSoup, target_date: date) -> Optional[Dict]:
        """嘗試下載 CSV 檔案"""
        try:
            # 尋找 CSV 下載連結
            links = soup.find_all('a', href=True)
            csv_links = [link for link in links if 'csv' in link.get('href', '').lower() or 'down' in link.get('href', '').lower()]
            
            if csv_links:
                csv_url = csv_links[0].get('href')
                if not csv_url.startswith('http'):
                    csv_url = f"{self.BASE_URL}{csv_url}"
                
                response = self.session.get(csv_url, timeout=30, verify=False)
                response.encoding = 'big5'
                
                if response.status_code == 200:
                    # 嘗試解析 CSV
                    df = pd.read_csv(StringIO(response.text), encoding='big5', engine='python')
                    # 這裡需要根據實際 CSV 格式解析
                    print(f"✅ 找到 CSV 下載連結，但需要根據實際格式調整解析邏輯")
                    return None
        
        except Exception as e:
            pass
        
        return None

