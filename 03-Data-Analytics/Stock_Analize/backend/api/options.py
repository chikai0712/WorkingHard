"""
選擇權相關 API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import date

from database.session import get_db
from database.models_futures import FuturesContract, OptionsDailyData, OptionsStrikeData

router = APIRouter()

@router.get("/open-interest", response_model=dict)
async def get_options_open_interest(
    period: str = Query("monthly", description="期間類型 (weekly=周選擇權, monthly=月選擇權)"),
    start_date: Optional[date] = Query(None, description="開始日期"),
    end_date: Optional[date] = Query(None, description="結束日期"),
    limit: int = Query(30, ge=1, le=365)
):
    """取得選擇權未平倉量資料"""
    db = next(get_db())
    try:
        query = db.query(OptionsDailyData).filter(
            OptionsDailyData.contract_period == period
        )
        
        if start_date:
            query = query.filter(OptionsDailyData.date >= start_date)
        if end_date:
            query = query.filter(OptionsDailyData.date <= end_date)
        
        data = query.order_by(OptionsDailyData.date.desc()).limit(limit).all()
        
        result = []
        for item in data:
            result.append({
                "date": item.date.isoformat(),
                "contract_code": item.contract_code,
                "contract_period": item.contract_period,
                "index_price": float(item.index_price) if item.index_price else None,
                "change": float(item.change) if item.change else None,
                "change_percent": float(item.change_percent) if item.change_percent else None,
                "call_volume": item.call_volume,
                "put_volume": item.put_volume,
                "total_volume": item.total_volume,
                "call_oi": item.call_oi,
                "put_oi": item.put_oi,
                "total_oi": item.total_oi,
                "pc_ratio_volume": float(item.pc_ratio_volume) if item.pc_ratio_volume else None,
                "pc_ratio_oi": float(item.pc_ratio_oi) if item.pc_ratio_oi else None,
                "foreign": {
                    "net_volume": item.foreign_net_volume,
                    "oi": item.foreign_oi,
                    "oi_change": item.foreign_oi_change
                },
                "trust": {
                    "net_volume": item.trust_net_volume,
                    "oi": item.trust_oi,
                    "oi_change": item.trust_oi_change
                },
                "dealer": {
                    "net_volume": item.dealer_net_volume,
                    "oi": item.dealer_oi,
                    "oi_change": item.dealer_oi_change
                }
            })
        
        return {
            "status": "success",
            "period": period,
            "data": result,
            "total": len(result)
        }
    finally:
        db.close()

@router.get("/strike-data", response_model=dict)
async def get_options_strike_data(
    period: str = Query("weekly", description="期間類型 (weekly=周選擇權, monthly=月選擇權)"),
    contract_code: Optional[str] = Query(None, description="合約代號 (如: 202512F3)"),
    target_date: Optional[date] = Query(None, description="目標日期 YYYY-MM-DD"),
    strike_range: Optional[str] = Query(None, description="履約價範圍 (例如: 26800-28400)")
):
    """取得選擇權履約價分布資料（買權OI和賣權OI）"""
    db = next(get_db())
    try:
        if target_date is None:
            target_date = date.today()
        
        # 取得選擇權每日資料
        query = db.query(OptionsDailyData).filter(
            OptionsDailyData.date == target_date,
            OptionsDailyData.contract_period == period
        )
        
        if contract_code:
            query = query.filter(OptionsDailyData.contract_code == contract_code)
        
        options_daily = query.order_by(OptionsDailyData.date.desc()).first()
        
        if not options_daily:
            raise HTTPException(
                status_code=404,
                detail=f"找不到 {target_date} 的 {period} 選擇權資料"
            )
        
        # 取得履約價資料
        strike_query = db.query(OptionsStrikeData).filter(
            OptionsStrikeData.options_daily_id == options_daily.id
        )
        
        if strike_range:
            # 解析履約價範圍
            try:
                min_strike, max_strike = map(float, strike_range.split('-'))
                strike_query = strike_query.filter(
                    OptionsStrikeData.strike_price >= min_strike,
                    OptionsStrikeData.strike_price <= max_strike
                )
            except:
                pass
        
        strike_data_list = strike_query.order_by(OptionsStrikeData.strike_price).all()
        
        result = []
        for item in strike_data_list:
            result.append({
                "strike_price": float(item.strike_price),
                "call": {
                    "oi": item.call_oi,
                    "oi_change": item.call_oi_change,
                    "volume": item.call_volume
                },
                "put": {
                    "oi": item.put_oi,
                    "oi_change": item.put_oi_change,
                    "volume": item.put_volume
                }
            })
        
        return {
            "status": "success",
            "date": target_date.isoformat(),
            "contract_code": options_daily.contract_code,
            "contract_period": period,
            "index_price": float(options_daily.index_price) if options_daily.index_price else None,
            "strike_data": result,
            "total": len(result)
        }
    finally:
        db.close()

@router.get("/daily", response_model=dict)
async def get_options_daily_data(
    period: str = Query("monthly", description="期間類型"),
    start_date: Optional[date] = Query(None, description="開始日期"),
    end_date: Optional[date] = Query(None, description="結束日期"),
    limit: int = Query(30, ge=1, le=365)
):
    """取得選擇權每日交易資料（歷史）"""
    db = next(get_db())
    try:
        query = db.query(OptionsDailyData).filter(
            OptionsDailyData.contract_period == period
        )
        
        if start_date:
            query = query.filter(OptionsDailyData.date >= start_date)
        if end_date:
            query = query.filter(OptionsDailyData.date <= end_date)
        
        data = query.order_by(OptionsDailyData.date.desc()).limit(limit).all()
        
        result = []
        for item in data:
            result.append({
                "date": item.date.isoformat(),
                "contract_code": item.contract_code,
                "index_price": float(item.index_price) if item.index_price else None,
                "change": float(item.change) if item.change else None,
                "change_percent": float(item.change_percent) if item.change_percent else None,
                "call_volume": item.call_volume,
                "put_volume": item.put_volume,
                "total_volume": item.total_volume,
                "pc_ratio_volume": float(item.pc_ratio_volume) if item.pc_ratio_volume else None,
                "foreign_net_volume": item.foreign_net_volume,
                "trust_net_volume": item.trust_net_volume,
                "dealer_net_volume": item.dealer_net_volume,
                "foreign_oi": item.foreign_oi,
                "foreign_oi_change": item.foreign_oi_change,
                "trust_oi": item.trust_oi,
                "trust_oi_change": item.trust_oi_change,
                "dealer_oi": item.dealer_oi,
                "dealer_oi_change": item.dealer_oi_change,
                "pc_ratio_oi": float(item.pc_ratio_oi) if item.pc_ratio_oi else None
            })
        
        return {
            "status": "success",
            "period": period,
            "data": result,
            "total": len(result)
        }
    finally:
        db.close()

