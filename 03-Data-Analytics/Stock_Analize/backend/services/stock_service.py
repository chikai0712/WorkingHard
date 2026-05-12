"""
股票服務層
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List, Tuple
from datetime import date

from database.models import Stock, StockPrice

class StockService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_stocks(
        self,
        market: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Stock], int]:
        """取得股票列表"""
        query = self.db.query(Stock).filter(Stock.is_active == True)
        
        if market:
            query = query.filter(Stock.market == market)
        
        total = query.count()
        stocks = query.order_by(Stock.symbol).offset(skip).limit(limit).all()
        
        return stocks, total
    
    def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """根據代號取得股票"""
        return self.db.query(Stock).filter(Stock.symbol == symbol).first()
    
    def get_stock_by_id(self, stock_id: int) -> Optional[Stock]:
        """根據 ID 取得股票"""
        return self.db.query(Stock).filter(Stock.id == stock_id).first()
    
    def create_stock(
        self,
        symbol: str,
        market: str,
        name: str,
        industry: Optional[str] = None
    ) -> Stock:
        """建立新股票"""
        stock = Stock(
            symbol=symbol,
            market=market,
            name=name,
            industry=industry
        )
        self.db.add(stock)
        self.db.commit()
        self.db.refresh(stock)
        return stock
    
    def delete_stock(self, stock_id: int) -> bool:
        """刪除股票（軟刪除）"""
        stock = self.get_stock_by_id(stock_id)
        if stock:
            stock.is_active = False
            self.db.commit()
            return True
        return False
    
    def get_latest_price(self, stock_id: int) -> Optional[StockPrice]:
        """取得最新價格"""
        return (
            self.db.query(StockPrice)
            .filter(StockPrice.stock_id == stock_id)
            .order_by(desc(StockPrice.date))
            .first()
        )
    
    def get_price_history(
        self,
        stock_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[StockPrice], int]:
        """取得歷史價格"""
        query = self.db.query(StockPrice).filter(StockPrice.stock_id == stock_id)
        
        if start_date:
            query = query.filter(StockPrice.date >= start_date)
        if end_date:
            query = query.filter(StockPrice.date <= end_date)
        
        total = query.count()
        prices = (
            query.order_by(desc(StockPrice.date))
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        return prices, total

