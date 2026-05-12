"""
期貨相關 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import date
from pydantic import BaseModel

from database.session import get_db
from database.models_futures import FuturesContract, FuturesDailyData, InstitutionalTradingData, FuturesOpenInterest

router = APIRouter()

# 注意：期貨相關 API 路由前綴為 /api/futures

# Pydantic 模型
class FuturesDailyDataResponse(BaseModel):
    date: date
    contract_code: Optional[str]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    settlement: Optional[float]
    change: Optional[float]
    change_percent: Optional[float]
    volume: Optional[int]
    open_interest: Optional[int]
    
    class Config:
        from_attributes = True

class InstitutionalTradingResponse(BaseModel):
    date: date
    market_type: Optional[str]
    foreign_net: Optional[float]
    trust_net: Optional[float]
    dealer_net: Optional[float]
    total_net: Optional[float]
    
    class Config:
        from_attributes = True

@router.get("/daily", response_model=dict)
async def get_futures_daily_data(
    symbol: str = Query("TX", description="期貨代號 (TX=台指期貨, MTX=小型台指期貨)"),
    start_date: Optional[date] = Query(None, description="開始日期 YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="結束日期 YYYY-MM-DD"),
    limit: int = Query(30, ge=1, le=365)
):
    """取得期貨每日交易資料"""
    db = next(get_db())
    try:
        # 取得合約
        contract = db.query(FuturesContract).filter(
            FuturesContract.symbol == symbol
        ).first()
        
        if not contract:
            raise HTTPException(status_code=404, detail=f"找不到期貨合約: {symbol}")
        
        # 查詢資料
        query = db.query(FuturesDailyData).filter(
            FuturesDailyData.contract_id == contract.id
        )
        
        if start_date:
            query = query.filter(FuturesDailyData.date >= start_date)
        if end_date:
            query = query.filter(FuturesDailyData.date <= end_date)
        
        data = query.order_by(FuturesDailyData.date.desc()).limit(limit).all()
        
        result = []
        for item in data:
            result.append({
                "date": item.date.isoformat(),
                "contract_code": item.contract_code,
                "open": float(item.open) if item.open else None,
                "high": float(item.high) if item.high else None,
                "low": float(item.low) if item.low else None,
                "close": float(item.close) if item.close else None,
                "settlement": float(item.settlement) if item.settlement else None,
                "change": float(item.change) if item.change else None,
                "change_percent": float(item.change_percent) if item.change_percent else None,
                "volume": item.volume,
                "open_interest": item.open_interest
            })
        
        return {
            "status": "success",
            "symbol": symbol,
            "data": result,
            "total": len(result)
        }
    finally:
        db.close()

@router.get("/institutional", response_model=dict)
async def get_institutional_trading(
    market_type: str = Query("weighted", description="市場類型 (weighted=加權指數, otc=櫃買指數)"),
    start_date: Optional[date] = Query(None, description="開始日期"),
    end_date: Optional[date] = Query(None, description="結束日期"),
    limit: int = Query(30, ge=1, le=365)
):
    """取得三大法人買賣超資料"""
    db = next(get_db())
    try:
        query = db.query(InstitutionalTradingData).filter(
            InstitutionalTradingData.market_type == market_type
        )
        
        if start_date:
            query = query.filter(InstitutionalTradingData.date >= start_date)
        if end_date:
            query = query.filter(InstitutionalTradingData.date <= end_date)
        
        data = query.order_by(InstitutionalTradingData.date.desc()).limit(limit).all()
        
        result = []
        for item in data:
            result.append({
                "date": item.date.isoformat(),
                "market_type": item.market_type,
                "foreign": {
                    "buy": float(item.foreign_buy) if item.foreign_buy else None,
                    "sell": float(item.foreign_sell) if item.foreign_sell else None,
                    "net": float(item.foreign_net) if item.foreign_net else None
                },
                "trust": {
                    "buy": float(item.trust_buy) if item.trust_buy else None,
                    "sell": float(item.trust_sell) if item.trust_sell else None,
                    "net": float(item.trust_net) if item.trust_net else None
                },
                "dealer": {
                    "buy": float(item.dealer_buy) if item.dealer_buy else None,
                    "sell": float(item.dealer_sell) if item.dealer_sell else None,
                    "net": float(item.dealer_net) if item.dealer_net else None,
                    "self_buy": float(item.dealer_self_buy) if item.dealer_self_buy else None,
                    "self_sell": float(item.dealer_self_sell) if item.dealer_self_sell else None,
                    "self_net": float(item.dealer_self_net) if item.dealer_self_net else None,
                    "hedge_buy": float(item.dealer_hedge_buy) if item.dealer_hedge_buy else None,
                    "hedge_sell": float(item.dealer_hedge_sell) if item.dealer_hedge_sell else None,
                    "hedge_net": float(item.dealer_hedge_net) if item.dealer_hedge_net else None
                },
                "total_net": float(item.total_net) if item.total_net else None
            })
        
        return {
            "status": "success",
            "market_type": market_type,
            "data": result,
            "total": len(result)
        }
    finally:
        db.close()

@router.get("/open-interest", response_model=dict)
async def get_futures_open_interest(
    symbol: str = Query("TX", description="期貨代號"),
    start_date: Optional[date] = Query(None, description="開始日期"),
    end_date: Optional[date] = Query(None, description="結束日期"),
    limit: int = Query(30, ge=1, le=365)
):
    """取得期貨未平倉量資料"""
    db = next(get_db())
    try:
        contract = db.query(FuturesContract).filter(
            FuturesContract.symbol == symbol
        ).first()
        
        if not contract:
            raise HTTPException(status_code=404, detail=f"找不到期貨合約: {symbol}")
        
        query = db.query(FuturesOpenInterest).filter(
            FuturesOpenInterest.contract_id == contract.id
        )
        
        if start_date:
            query = query.filter(FuturesOpenInterest.date >= start_date)
        if end_date:
            query = query.filter(FuturesOpenInterest.date <= end_date)
        
        data = query.order_by(FuturesOpenInterest.date.desc()).limit(limit).all()
        
        result = []
        for item in data:
            result.append({
                "date": item.date.isoformat(),
                "foreign": {
                    "oi": item.foreign_oi,
                    "oi_change": item.foreign_oi_change
                },
                "trust": {
                    "oi": item.trust_oi,
                    "oi_change": item.trust_oi_change
                },
                "dealer": {
                    "oi": item.dealer_oi,
                    "oi_change": item.dealer_oi_change
                },
                "top5": {
                    "oi": item.top5_oi,
                    "oi_change": item.top10_oi - item.top5_oi if item.top5_oi and item.top10_oi else None
                },
                "top10": {
                    "oi": item.top10_oi,
                    "oi_change": None
                },
                "top5_special": {
                    "oi": item.top5_special_oi,
                    "oi_change": item.top10_special_oi - item.top5_special_oi if item.top5_special_oi and item.top10_special_oi else None
                },
                "top10_special": {
                    "oi": item.top10_special_oi,
                    "oi_change": None
                },
                "retail": {
                    "oi": item.retail_oi,
                    "oi_change": item.retail_oi_change
                }
            })
        
        return {
            "status": "success",
            "symbol": symbol,
            "data": result,
            "total": len(result)
        }
    finally:
        db.close()

