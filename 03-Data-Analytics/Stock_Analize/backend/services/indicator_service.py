"""
技術指標服務層
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import Optional, List
from datetime import date

from database.models import TechnicalIndicator

class IndicatorService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_indicators(
        self,
        stock_id: int,
        target_date: Optional[date] = None
    ) -> List[TechnicalIndicator]:
        """取得所有技術指標"""
        query = self.db.query(TechnicalIndicator).filter(
            TechnicalIndicator.stock_id == stock_id
        )
        
        if target_date:
            query = query.filter(TechnicalIndicator.date == target_date)
        else:
            # 取得最新日期的所有指標
            latest_date = (
                self.db.query(TechnicalIndicator.date)
                .filter(TechnicalIndicator.stock_id == stock_id)
                .order_by(desc(TechnicalIndicator.date))
                .first()
            )
            if latest_date:
                query = query.filter(TechnicalIndicator.date == latest_date[0])
        
        return query.all()
    
    def get_indicator(
        self,
        stock_id: int,
        indicator_type: str,
        period: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TechnicalIndicator]:
        """取得特定技術指標"""
        query = self.db.query(TechnicalIndicator).filter(
            and_(
                TechnicalIndicator.stock_id == stock_id,
                TechnicalIndicator.indicator_type == indicator_type
            )
        )
        
        if period:
            query = query.filter(TechnicalIndicator.period == period)
        if start_date:
            query = query.filter(TechnicalIndicator.date >= start_date)
        if end_date:
            query = query.filter(TechnicalIndicator.date <= end_date)
        
        return query.order_by(desc(TechnicalIndicator.date)).all()

