"""
股票列表相關 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database.models import Stock
from database.session import get_db
from services.stock_service import StockService

router = APIRouter()

# Pydantic 模型
class StockResponse(BaseModel):
    id: int
    symbol: str
    market: str
    name: str
    industry: Optional[str] = None
    current_price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StockCreate(BaseModel):
    symbol: str
    market: str
    name: str
    industry: Optional[str] = None

class StockListResponse(BaseModel):
    status: str
    data: List[StockResponse]
    total: int

@router.get("", response_model=StockListResponse)
async def get_stocks(
    market: Optional[str] = Query(None, description="市場過濾（TW/US）"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """取得所有監控股票列表"""
    db = next(get_db())
    try:
        stock_service = StockService(db)
        stocks, total = stock_service.get_stocks(market=market, skip=skip, limit=limit)
        
        # 轉換為回應格式
        stock_list = []
        for stock in stocks:
            # 取得最新價格資訊
            latest_price = stock_service.get_latest_price(stock.id)
            stock_data = StockResponse(
                id=stock.id,
                symbol=stock.symbol,
                market=stock.market,
                name=stock.name,
                industry=stock.industry,
                current_price=latest_price.close if latest_price else None,
                change=latest_price.change_amount if latest_price else None,
                change_percent=latest_price.change_percent if latest_price else None,
                volume=latest_price.volume if latest_price else None,
                updated_at=latest_price.updated_at if latest_price else None
            )
            stock_list.append(stock_data)
        
        return StockListResponse(
            status="success",
            data=stock_list,
            total=total
        )
    finally:
        db.close()

@router.get("/{symbol}", response_model=dict)
async def get_stock(symbol: str):
    """取得特定股票資訊"""
    db = next(get_db())
    try:
        stock_service = StockService(db)
        stock = stock_service.get_stock_by_symbol(symbol)
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"找不到股票代號: {symbol}")
        
        latest_price = stock_service.get_latest_price(stock.id)
        
        return {
            "status": "success",
            "data": {
                "id": stock.id,
                "symbol": stock.symbol,
                "market": stock.market,
                "name": stock.name,
                "industry": stock.industry,
                "full_name": stock.full_name,
                "description": stock.description,
                "website": stock.website,
                "current_price": latest_price.close if latest_price else None,
                "change": latest_price.change_amount if latest_price else None,
                "change_percent": latest_price.change_percent if latest_price else None,
                "volume": latest_price.volume if latest_price else None,
                "updated_at": latest_price.updated_at if latest_price else None
            }
        }
    finally:
        db.close()

@router.post("", response_model=dict)
async def create_stock(stock_data: StockCreate):
    """新增監控股票"""
    db = next(get_db())
    try:
        stock_service = StockService(db)
        
        # 檢查是否已存在
        existing = stock_service.get_stock_by_symbol(stock_data.symbol)
        if existing:
            raise HTTPException(status_code=400, detail=f"股票 {stock_data.symbol} 已存在")
        
        stock = stock_service.create_stock(
            symbol=stock_data.symbol,
            market=stock_data.market,
            name=stock_data.name,
            industry=stock_data.industry
        )
        
        return {
            "status": "success",
            "message": "股票已新增",
            "data": {
                "id": stock.id,
                "symbol": stock.symbol,
                "market": stock.market,
                "name": stock.name
            }
        }
    finally:
        db.close()

@router.delete("/{symbol}", response_model=dict)
async def delete_stock(symbol: str):
    """移除監控股票"""
    db = next(get_db())
    try:
        stock_service = StockService(db)
        stock = stock_service.get_stock_by_symbol(symbol)
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"找不到股票代號: {symbol}")
        
        stock_service.delete_stock(stock.id)
        
        return {
            "status": "success",
            "message": "股票已移除"
        }
    finally:
        db.close()

