"""
股票價格相關 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel

from database.models import Stock
from database.session import get_db
from services.stock_service import StockService

router = APIRouter()

class PriceResponse(BaseModel):
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: Optional[float] = None
    change_percent: Optional[float] = None
    updated_at: datetime

@router.get("/{symbol}/price", response_model=dict)
async def get_latest_price(symbol: str):
    """取得最新價格"""
    db = next(get_db())
    try:
        stock_service = StockService(db)
        stock = stock_service.get_stock_by_symbol(symbol)
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"找不到股票代號: {symbol}")
        
        latest_price = stock_service.get_latest_price(stock.id)
        
        if not latest_price:
            raise HTTPException(status_code=404, detail=f"找不到 {symbol} 的價格資料")
        
        return {
            "status": "success",
            "data": {
                "symbol": stock.symbol,
                "date": latest_price.date,
                "open": float(latest_price.open),
                "high": float(latest_price.high),
                "low": float(latest_price.low),
                "close": float(latest_price.close),
                "volume": latest_price.volume,
                "change": float(latest_price.change_amount) if latest_price.change_amount else None,
                "change_percent": float(latest_price.change_percent) if latest_price.change_percent else None,
                "updated_at": latest_price.updated_at
            }
        }
    finally:
        db.close()

@router.get("/{symbol}/history", response_model=dict)
async def get_price_history(
    symbol: str,
    start_date: Optional[date] = Query(None, description="開始日期 YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="結束日期 YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """取得歷史價格資料"""
    db = next(get_db())
    try:
        stock_service = StockService(db)
        stock = stock_service.get_stock_by_symbol(symbol)
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"找不到股票代號: {symbol}")
        
        prices, total = stock_service.get_price_history(
            stock.id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        price_list = [
            {
                "date": price.date,
                "open": float(price.open),
                "high": float(price.high),
                "low": float(price.low),
                "close": float(price.close),
                "volume": price.volume,
                "change": float(price.change_amount) if price.change_amount else None,
                "change_percent": float(price.change_percent) if price.change_percent else None
            }
            for price in prices
        ]
        
        return {
            "status": "success",
            "data": price_list,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    finally:
        db.close()

