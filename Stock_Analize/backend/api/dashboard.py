"""
儀表板統計相關 API
"""

from fastapi import APIRouter, Query
from typing import Optional

from database.session import get_db
from services.dashboard_service import DashboardService

router = APIRouter()

@router.get("/summary", response_model=dict)
async def get_dashboard_summary():
    """取得儀表板摘要統計"""
    db = next(get_db())
    try:
        dashboard_service = DashboardService(db)
        summary = dashboard_service.get_summary()
        
        return {
            "status": "success",
            "data": summary
        }
    finally:
        db.close()

@router.get("/top-gainers", response_model=dict)
async def get_top_gainers(limit: int = Query(10, ge=1, le=100)):
    """取得漲幅排行榜"""
    db = next(get_db())
    try:
        dashboard_service = DashboardService(db)
        gainers = dashboard_service.get_top_gainers(limit=limit)
        
        return {
            "status": "success",
            "data": gainers
        }
    finally:
        db.close()

@router.get("/top-losers", response_model=dict)
async def get_top_losers(limit: int = Query(10, ge=1, le=100)):
    """取得跌幅排行榜"""
    db = next(get_db())
    try:
        dashboard_service = DashboardService(db)
        losers = dashboard_service.get_top_losers(limit=limit)
        
        return {
            "status": "success",
            "data": losers
        }
    finally:
        db.close()

