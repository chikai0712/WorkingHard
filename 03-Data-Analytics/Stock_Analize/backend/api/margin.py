"""
融資融券相關 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import date

from database.session import get_db
from database.models_futures import MarginTradingData

router = APIRouter()

@router.get("/trading", response_model=dict)
async def get_margin_trading(
    market_type: str = Query("weighted", description="市場類型 (weighted=加權指數, otc=櫃買指數)"),
    start_date: Optional[date] = Query(None, description="開始日期 YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="結束日期 YYYY-MM-DD"),
    limit: int = Query(30, ge=1, le=365)
):
    """取得融資融券餘額資料"""
    db = next(get_db())
    try:
        query = db.query(MarginTradingData).filter(
            MarginTradingData.market_type == market_type
        )
        
        if start_date:
            query = query.filter(MarginTradingData.date >= start_date)
        if end_date:
            query = query.filter(MarginTradingData.date <= end_date)
        
        data = query.order_by(MarginTradingData.date.desc()).limit(limit).all()
        
        result = []
        for item in data:
            result.append({
                "date": item.date.isoformat(),
                "market_type": item.market_type,
                "margin": {
                    "balance": float(item.margin_balance) if item.margin_balance else None,  # 億元
                    "change": float(item.margin_change) if item.margin_change else None  # 億元
                },
                "short_selling": {
                    "balance": item.short_selling_balance,  # 張
                    "change": item.short_selling_change  # 張
                },
                "securities_lending": {
                    "sell": item.securities_lending_sell,  # 張
                    "change": item.securities_lending_change  # 張
                },
                "index": {
                    "price": float(item.index_price) if item.index_price else None,
                    "change_percent": float(item.index_change_percent) if item.index_change_percent else None
                }
            })
        
        return {
            "status": "success",
            "market_type": market_type,
            "data": result,
            "total": len(result)
        }
    finally:
        db.close()

