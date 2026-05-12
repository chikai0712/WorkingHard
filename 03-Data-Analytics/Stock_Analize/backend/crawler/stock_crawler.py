"""
股票資料抓取模組
支援多種資料來源：yfinance (歷史資料) 和 TWSE API (即時資料)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import time
import os

from database.models import Stock, StockPrice
from database.session import get_db
from services.stock_service import StockService

class StockCrawler:
    """股票資料抓取器"""
    
    def __init__(self, db: Session, use_realtime: bool = False):
        """
        初始化股票資料抓取器
        
        Args:
            db: 資料庫 Session
            use_realtime: 是否使用 TWSE 即時 API（約 20 秒延遲），預設 False（使用 yfinance）
        """
        self.db = db
        self.stock_service = StockService(db)
        self.use_realtime = use_realtime
        
        # 如果使用即時資料，初始化 TWSE 客戶端
        if self.use_realtime:
            try:
                from crawler.twse_realtime import TWSERealtimeClient
                self.twse_client = TWSERealtimeClient()
            except ImportError:
                print("⚠️ 無法載入 TWSE 即時客戶端，將使用 yfinance")
                self.use_realtime = False
    
    def fetch_stock_data(self, symbol: str, market: str = "TW") -> Optional[pd.DataFrame]:
        """
        抓取股票資料（支援 yfinance 和 TWSE 即時 API）
        
        Args:
            symbol: 股票代號
            market: 市場類型 ('TW', 'US') - 僅 TWSE API 支援台股
        
        Returns:
            DataFrame 包含股票資料，失敗返回 None
        """
        # 如果使用即時 API 且是台股，優先使用 TWSE
        if self.use_realtime and market == "TW":
            return self._fetch_from_twse(symbol)
        else:
            return self._fetch_from_yfinance(symbol, market)
    
    def _fetch_from_twse(self, symbol: str) -> Optional[pd.DataFrame]:
        """從 TWSE API 抓取即時資料（約 20 秒延遲）"""
        try:
            realtime_data = self.twse_client.get_stock_realtime(symbol)
            
            if not realtime_data:
                # 如果即時資料失敗，嘗試取得每日資料
                realtime_data = self.twse_client.get_stock_day(symbol)
            
            if not realtime_data:
                print(f"⚠️ 無法從 TWSE 取得 {symbol} 的資料")
                return None
            
            # 將單筆資料轉換為 DataFrame（與 yfinance 格式相容）
            df_data = {
                'Open': [realtime_data.get('open', 0)],
                'High': [realtime_data.get('high', 0)],
                'Low': [realtime_data.get('low', 0)],
                'Close': [realtime_data.get('close', 0)],
                'Volume': [realtime_data.get('volume', 0)],
            }
            
            df = pd.DataFrame(df_data, index=[pd.Timestamp(realtime_data.get('date', date.today()))])
            return df
        
        except Exception as e:
            print(f"❌ 從 TWSE 抓取 {symbol} 資料失敗: {str(e)}")
            # 失敗時回退到 yfinance
            return self._fetch_from_yfinance(symbol, "TW")
    
    def _fetch_from_yfinance(self, symbol: str, market: str = "TW") -> Optional[pd.DataFrame]:
        """從 yfinance 抓取股票資料（歷史資料，15-20 分鐘延遲）"""
        try:
            # yfinance 的股票代號格式
            # 台股需要加 .TW 後綴
            # 美股直接使用代號
            if market == "TW":
                yf_symbol = f"{symbol}.TW"
            else:
                yf_symbol = symbol
            
            # 抓取最近 30 天的資料
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                print(f"⚠️ 無法取得 {symbol} 的資料")
                return None
            
            return hist
        
        except Exception as e:
            print(f"❌ 抓取 {symbol} 資料時發生錯誤: {str(e)}")
            return None
    
    def save_price_data(self, stock_id: int, data: pd.DataFrame) -> int:
        """
        將抓取的資料儲存到資料庫
        
        Args:
            stock_id: 股票 ID
            data: yfinance 回傳的 DataFrame
        
        Returns:
            儲存的記錄數
        """
        saved_count = 0
        
        for idx, row in data.iterrows():
            try:
                # 轉換索引（日期）為 date 物件
                trade_date = idx.date() if isinstance(idx, pd.Timestamp) else idx
                
                # 檢查是否已存在
                existing = (
                    self.db.query(StockPrice)
                    .filter(
                        StockPrice.stock_id == stock_id,
                        StockPrice.date == trade_date
                    )
                    .first()
                )
                
                if existing:
                    # 更新現有記錄
                    existing.open = float(row['Open'])
                    existing.high = float(row['High'])
                    existing.low = float(row['Low'])
                    existing.close = float(row['Close'])
                    existing.volume = int(row['Volume']) if pd.notna(row['Volume']) else 0
                    existing.updated_at = datetime.utcnow()
                else:
                    # 計算漲跌
                    prev_price = (
                        self.db.query(StockPrice)
                        .filter(StockPrice.stock_id == stock_id)
                        .filter(StockPrice.date < trade_date)
                        .order_by(StockPrice.date.desc())
                        .first()
                    )
                    
                    change_amount = None
                    change_percent = None
                    if prev_price:
                        change_amount = float(row['Close']) - float(prev_price.close)
                        change_percent = (change_amount / float(prev_price.close)) * 100
                    
                    # 建立新記錄
                    price = StockPrice(
                        stock_id=stock_id,
                        date=trade_date,
                        open=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=int(row['Volume']) if pd.notna(row['Volume']) else 0,
                        change_amount=change_amount,
                        change_percent=change_percent
                    )
                    self.db.add(price)
                
                saved_count += 1
            
            except Exception as e:
                print(f"⚠️ 儲存 {trade_date} 的資料時發生錯誤: {str(e)}")
                continue
        
        try:
            self.db.commit()
            print(f"✅ 成功儲存 {saved_count} 筆 {stock_id} 的價格資料")
        except Exception as e:
            self.db.rollback()
            print(f"❌ 儲存資料時發生錯誤: {str(e)}")
            saved_count = 0
        
        return saved_count
    
    def update_all_stocks(self) -> Dict[str, int]:
        """
        更新所有監控股票的資料
        
        Returns:
            更新結果統計
        """
        stocks = self.db.query(Stock).filter(Stock.is_active == True).all()
        
        results = {
            "total": len(stocks),
            "success": 0,
            "failed": 0
        }
        
        for stock in stocks:
            try:
                print(f"📊 正在抓取 {stock.symbol} ({stock.name}) 的資料...")
                
                # 抓取資料
                data = self.fetch_stock_data(stock.symbol, stock.market)
                
                if data is not None and not data.empty:
                    # 儲存資料
                    saved_count = self.save_price_data(stock.id, data)
                    if saved_count > 0:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                else:
                    results["failed"] += 1
                
                # 避免請求過快
                time.sleep(1)
            
            except Exception as e:
                print(f"❌ 更新 {stock.symbol} 時發生錯誤: {str(e)}")
                results["failed"] += 1
        
        return results

