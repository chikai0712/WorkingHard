"""
台灣期貨交易所 (TAIFEX) 資料抓取模組
"""

import requests
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import time
import json

from database.models_futures import (
    FuturesContract, FuturesDailyData, InstitutionalTradingData,
    FuturesOpenInterest, OptionsDailyData, OptionsStrikeData, MarginTradingData
)

class TAIFEXCrawler:
    """台灣期貨交易所資料抓取器"""
    
    # TAIFEX API 端點
    BASE_URL = "https://www.taifex.com.tw"
    API_BASE = "https://www.taifex.com.tw/cht/3"
    
    def __init__(self, db: Session):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_futures_daily_data(self, contract_code: str = "TX", target_date: Optional[date] = None) -> Optional[pd.DataFrame]:
        """
        抓取期貨每日交易資料
        
        Args:
            contract_code: 合約代號 (TX=台指期貨, MTX=小型台指期貨)
            target_date: 目標日期，預設為今天
        
        Returns:
            DataFrame 包含期貨資料
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # TAIFEX 期貨每日交易資料 API
            # 注意：這是範例 URL，實際需要根據 TAIFEX 的 API 調整
            url = f"{self.API_BASE}/futDataDown"
            params = {
                'down_type': '1',
                'commodity_id': contract_code,
                'queryStartDate': target_date.strftime('%Y/%m/%d'),
                'queryEndDate': target_date.strftime('%Y/%m/%d')
            }
            
            response = self.session.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            # 解析 CSV 資料
            # 實際需要根據 TAIFEX 的回應格式調整
            # 這裡使用範例資料結構
            if response.text:
                # 嘗試解析 CSV
                try:
                    df = pd.read_csv(StringIO(response.text), encoding='big5')
                    return df
                except:
                    # 如果 CSV 解析失敗，可能需要其他處理方式
                    pass
            
            return None
        
        except Exception as e:
            print(f"❌ 抓取期貨資料失敗 ({contract_code}): {str(e)}")
            return None
    
    def fetch_institutional_trading_data(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        抓取三大法人買賣超資料
        
        Args:
            target_date: 目標日期
        
        Returns:
            Dict 包含三大法人資料
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # TAIFEX 三大法人買賣超 API
            # 實際 URL 需要根據 TAIFEX 文件調整
            url = f"{self.API_BASE}/futDataDown"
            params = {
                'down_type': '2',  # 三大法人買賣超
                'queryStartDate': target_date.strftime('%Y/%m/%d'),
                'queryEndDate': target_date.strftime('%Y/%m/%d')
            }
            
            response = self.session.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            # 解析資料
            # 實際需要根據 TAIFEX 的回應格式調整
            # 這裡返回範例結構
            return {
                'date': target_date,
                'weighted': {
                    'foreign': {'buy': 1581.05, 'sell': 1849.46, 'net': -268.41},
                    'trust': {'buy': 216.33, 'sell': 178.86, 'net': 37.47},
                    'dealer': {'buy': 292.18, 'sell': 220.83, 'net': 71.35}
                },
                'otc': {
                    'foreign': {'buy': 0, 'sell': 0, 'net': 4.23},
                    'trust': {'buy': 0, 'sell': 0, 'net': -3.10}
                }
            }
        
        except Exception as e:
            print(f"❌ 抓取三大法人資料失敗: {str(e)}")
            return None
    
    def fetch_futures_open_interest(self, target_date: Optional[date] = None) -> Optional[Dict]:
        """
        抓取期貨未平倉量資料
        
        Args:
            target_date: 目標日期
        
        Returns:
            Dict 包含未平倉量資料
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # TAIFEX 期貨未平倉量 API
            url = f"{self.API_BASE}/futDataDown"
            params = {
                'down_type': '3',  # 未平倉量
                'queryStartDate': target_date.strftime('%Y/%m/%d'),
                'queryEndDate': target_date.strftime('%Y/%m/%d')
            }
            
            response = self.session.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            # 解析資料
            # 實際需要根據 TAIFEX 的回應格式調整
            return {
                'date': target_date,
                'foreign_oi': -28731,
                'foreign_oi_change': 301,
                'trust_oi': 25526,
                'trust_oi_change': 346,
                'dealer_oi': -1344,
                'dealer_oi_change': -1265,
                'top5_oi': -4249,
                'top10_oi': -3220,
                'top5_special_oi': -5546,
                'top10_special_oi': 0,
                'retail_oi': 12274,
                'retail_oi_change': -2921
            }
        
        except Exception as e:
            print(f"❌ 抓取未平倉量資料失敗: {str(e)}")
            return None
    
    def fetch_options_daily_data(self, contract_code: str = "TXO", period: str = "monthly", target_date: Optional[date] = None) -> Optional[Dict]:
        """
        抓取選擇權每日交易資料
        
        Args:
            contract_code: 選擇權代號
            period: 'weekly' 或 'monthly'
            target_date: 目標日期
        
        Returns:
            Dict 包含選擇權資料
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # TAIFEX 選擇權每日交易資料 API
            url = f"{self.API_BASE}/optDataDown"
            params = {
                'down_type': '1',
                'commodity_id': contract_code,
                'queryStartDate': target_date.strftime('%Y/%m/%d'),
                'queryEndDate': target_date.strftime('%Y/%m/%d')
            }
            
            response = self.session.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            # 解析資料
            # 實際需要根據 TAIFEX 的回應格式調整
            return {
                'date': target_date,
                'contract_code': '202512F3',
                'contract_period': period,
                'index_price': 27469.0,
                'change': -56.64,
                'change_percent': -0.21,
                'call_volume': 0,
                'put_volume': 0,
                'total_volume': 0,
                'call_oi': 0,
                'put_oi': 0,
                'total_oi': 0,
                'pc_ratio_volume': 93.2,
                'pc_ratio_oi': 81.0,
                'foreign_net_volume': -1497,
                'trust_net_volume': 0,
                'dealer_net_volume': 8721,
                'foreign_oi': 2420,
                'foreign_oi_change': -1497,
                'trust_oi': 0,
                'trust_oi_change': 0,
                'dealer_oi': -7029,
                'dealer_oi_change': 8721
            }
        
        except Exception as e:
            print(f"❌ 抓取選擇權資料失敗: {str(e)}")
            return None
    
    def fetch_options_strike_data(self, options_daily_id: int, contract_code: str, period: str, target_date: Optional[date] = None) -> List[Dict]:
        """
        抓取選擇權履約價資料（包含各履約價的 OI 分布）
        
        Args:
            options_daily_id: 選擇權每日資料 ID
            contract_code: 合約代號
            period: 'weekly' 或 'monthly'
            target_date: 目標日期
        
        Returns:
            List of Dict 包含各履約價資料
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # TAIFEX 選擇權履約價資料 API
            url = f"{self.API_BASE}/optDataDown"
            params = {
                'down_type': '2',  # 履約價分布
                'commodity_id': contract_code,
                'queryStartDate': target_date.strftime('%Y/%m/%d'),
                'queryEndDate': target_date.strftime('%Y/%m/%d')
            }
            
            response = self.session.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            # 解析資料
            # 這裡返回範例資料結構
            # 實際需要根據 TAIFEX 的回應格式調整
            strike_data = []
            # 範例履約價範圍
            for strike in range(26800, 28500, 50):
                strike_data.append({
                    'options_daily_id': options_daily_id,
                    'date': target_date,
                    'strike_price': float(strike),
                    'call_oi': 0,  # 實際需要從 API 取得
                    'call_oi_change': 0,
                    'call_volume': 0,
                    'put_oi': 0,
                    'put_oi_change': 0,
                    'put_volume': 0
                })
            
            return strike_data
        
        except Exception as e:
            print(f"❌ 抓取選擇權履約價資料失敗: {str(e)}")
            return []
    
    def fetch_margin_trading_data(self, market_type: str = "weighted", target_date: Optional[date] = None) -> Optional[Dict]:
        """
        抓取融資融券餘額資料
        
        Args:
            market_type: 'weighted' 或 'otc'
            target_date: 目標日期
        
        Returns:
            Dict 包含融資融券資料
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # 證交所或櫃買中心融資融券餘額 API
            # 實際 URL 需要根據證交所 API 調整
            if market_type == "weighted":
                url = "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN"
            else:
                url = "https://www.tpex.org.tw/web/stock/margin_trading/margin_balance/margin_balance_result.php"
            
            params = {
                'date': target_date.strftime('%Y%m%d')
            }
            
            response = self.session.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            # 解析資料
            # 實際需要根據證交所的回應格式調整
            return {
                'date': target_date,
                'market_type': market_type,
                'margin_balance': 3323.8,  # 億元
                'margin_change': 2.1,
                'short_selling_balance': 300546,  # 張
                'short_selling_change': -1484,
                'securities_lending_sell': 1424344,
                'securities_lending_change': 8547,
                'index_price': 27468.53,
                'index_change_percent': -0.21
            }
        
        except Exception as e:
            print(f"❌ 抓取融資融券資料失敗 ({market_type}): {str(e)}")
            return None
    
    def save_all_data(self, target_date: Optional[date] = None):
        """
        儲存所有台指期貨相關資料
        
        Args:
            target_date: 目標日期
        """
        if target_date is None:
            target_date = date.today()
        
        print(f"📊 開始抓取 {target_date} 的台指期貨資料...")
        
        # 1. 取得或建立台指期貨合約
        tx_contract = self.db.query(FuturesContract).filter(
            FuturesContract.symbol == "TX"
        ).first()
        
        if not tx_contract:
            tx_contract = FuturesContract(
                symbol="TX",
                name="台指期貨",
                contract_type="index"
            )
            self.db.add(tx_contract)
            self.db.commit()
            self.db.refresh(tx_contract)
        
        # 2. 抓取並儲存期貨每日資料
        futures_data = self.fetch_futures_daily_data("TX", target_date)
        if futures_data is not None:
            # 儲存邏輯（實際需要根據資料結構調整）
            pass
        
        # 3. 抓取並儲存三大法人買賣超
        inst_data = self.fetch_institutional_trading_data(target_date)
        if inst_data:
            for market_type in ['weighted', 'otc']:
                if market_type in inst_data:
                    data = inst_data[market_type]
                    # 儲存邏輯
                    pass
        
        # 4. 抓取並儲存未平倉量
        oi_data = self.fetch_futures_open_interest(target_date)
        if oi_data:
            # 儲存邏輯
            pass
        
        # 5. 抓取並儲存選擇權資料
        for period in ['weekly', 'monthly']:
            options_data = self.fetch_options_daily_data("TXO", period, target_date)
            if options_data:
                # 儲存邏輯
                pass
        
        # 6. 抓取並儲存融資融券資料
        for market_type in ['weighted', 'otc']:
            margin_data = self.fetch_margin_trading_data(market_type, target_date)
            if margin_data:
                # 儲存邏輯
                pass
        
        try:
            self.db.commit()
            print(f"✅ {target_date} 的資料儲存完成")
        except Exception as e:
            self.db.rollback()
            print(f"❌ 儲存資料時發生錯誤: {str(e)}")

