"""
技術指標相關 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict
from datetime import date

from database.session import get_db
from services.stock_service import StockService
from services.indicator_service import IndicatorService

router = APIRouter()

@router.get("/{symbol}/indicators", response_model=dict)
async def get_indicators(
    symbol: str,
    target_date: Optional[date] = Query(None, alias="date", description="查詢日期 YYYY-MM-DD")
):
    """取得所有技術指標"""
    db = next(get_db())
    try:
        stock_service = StockService(db)
        indicator_service = IndicatorService(db)
        
        stock = stock_service.get_stock_by_symbol(symbol)
        if not stock:
            raise HTTPException(status_code=404, detail=f"找不到股票代號: {symbol}")
        
        indicators = indicator_service.get_all_indicators(stock.id, target_date)
        
        # 組織指標資料
        indicators_dict = {}
        for indicator in indicators:
            key = indicator.indicator_name
            if indicator.indicator_type == "MACD" and indicator.extra_data:
                # MACD 需要額外處理
                indicators_dict[key] = {
                    "value": float(indicator.value),
                    "signal": indicator.extra_data.get("signal"),
                    "hist": indicator.extra_data.get("hist")
                }
            else:
                indicators_dict[key] = float(indicator.value)
        
        return {
            "status": "success",
            "data": {
                "symbol": stock.symbol,
                "date": target_date or indicators[0].date if indicators else None,
                "indicators": indicators_dict
            }
        }
    finally:
        db.close()

@router.get("/{symbol}/indicators/{indicator_type}", response_model=dict)
async def get_indicator(
    symbol: str,
    indicator_type: str,
    period: Optional[int] = Query(None, description="計算週期"),
    start_date: Optional[date] = Query(None, description="開始日期"),
    end_date: Optional[date] = Query(None, description="結束日期")
):
    """取得特定技術指標"""
    db = next(get_db())
    try:
        stock_service = StockService(db)
        indicator_service = IndicatorService(db)
        
        stock = stock_service.get_stock_by_symbol(symbol)
        if not stock:
            raise HTTPException(status_code=404, detail=f"找不到股票代號: {symbol}")
        
        indicators = indicator_service.get_indicator(
            stock.id,
            indicator_type,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        values = [
            {
                "date": indicator.date,
                "value": float(indicator.value),
                "period": indicator.period
            }
            for indicator in indicators
        ]
        
        return {
            "status": "success",
            "data": {
                "symbol": stock.symbol,
                "indicator_type": indicator_type,
                "period": period,
                "values": values
            }
        }
    finally:
        db.close()

