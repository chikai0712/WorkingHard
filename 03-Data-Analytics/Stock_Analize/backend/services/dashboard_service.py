"""
儀表板服務層
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Dict
from datetime import datetime

from database.models import Stock, StockPrice

class DashboardService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_summary(self) -> Dict:
        """取得儀表板摘要統計"""
        # 總股票數
        total_stocks = self.db.query(Stock).filter(Stock.is_active == True).count()
        
        # 取得所有活躍股票的最新價格
        stocks = self.db.query(Stock).filter(Stock.is_active == True).all()
        
        total_value = 0.0
        total_change = 0.0
        gaining_count = 0
        losing_count = 0
        unchanged_count = 0
        
        for stock in stocks:
            latest_price = (
                self.db.query(StockPrice)
                .filter(StockPrice.stock_id == stock.id)
                .order_by(desc(StockPrice.date))
                .first()
            )
            
            if latest_price and latest_price.close:
                total_value += float(latest_price.close)
                if latest_price.change_amount:
                    total_change += float(latest_price.change_amount)
                    if latest_price.change_amount > 0:
                        gaining_count += 1
                    elif latest_price.change_amount < 0:
                        losing_count += 1
                    else:
                        unchanged_count += 1
        
        total_change_percent = (total_change / total_value * 100) if total_value > 0 else 0.0
        
        return {
            "total_stocks": total_stocks,
            "total_value": round(total_value, 2),
            "total_change": round(total_change, 2),
            "total_change_percent": round(total_change_percent, 2),
            "gaining_stocks": gaining_count,
            "losing_stocks": losing_count,
            "unchanged_stocks": unchanged_count,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
    
    def get_top_gainers(self, limit: int = 10) -> List[Dict]:
        """取得漲幅排行榜"""
        # 取得所有活躍股票
        stocks = self.db.query(Stock).filter(Stock.is_active == True).all()
        
        gainers = []
        for stock in stocks:
            latest_price = (
                self.db.query(StockPrice)
                .filter(StockPrice.stock_id == stock.id)
                .order_by(desc(StockPrice.date))
                .first()
            )
            
            if latest_price and latest_price.change_percent and latest_price.change_percent > 0:
                gainers.append({
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "change": float(latest_price.change_amount) if latest_price.change_amount else 0.0,
                    "change_percent": float(latest_price.change_percent),
                    "current_price": float(latest_price.close)
                })
        
        # 依漲幅排序
        gainers.sort(key=lambda x: x["change_percent"], reverse=True)
        
        return gainers[:limit]
    
    def get_top_losers(self, limit: int = 10) -> List[Dict]:
        """取得跌幅排行榜"""
        stocks = self.db.query(Stock).filter(Stock.is_active == True).all()
        
        losers = []
        for stock in stocks:
            latest_price = (
                self.db.query(StockPrice)
                .filter(StockPrice.stock_id == stock.id)
                .order_by(desc(StockPrice.date))
                .first()
            )
            
            if latest_price and latest_price.change_percent and latest_price.change_percent < 0:
                losers.append({
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "change": float(latest_price.change_amount) if latest_price.change_amount else 0.0,
                    "change_percent": float(latest_price.change_percent),
                    "current_price": float(latest_price.close)
                })
        
        # 依跌幅排序（負數，所以升序）
        losers.sort(key=lambda x: x["change_percent"])
        
        return losers[:limit]

