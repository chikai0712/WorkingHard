"""
GlobalpingChecker V4 - FastAPI Web Application
提供 Web Dashboard 和 API 介面
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from .config import get_settings
from .database import (
    get_db, init_db, TestBatch, DomainResult, NodeDetail, 
    DomainHistory, SchedulerLog, DomainStatus
)
from .scheduler import start_scheduler, stop_scheduler, run_once
from .checker import run_check

settings = get_settings()

app = FastAPI(
    title="GlobalpingChecker V4",
    description="域名監控系統 - 印尼 ISP DNS 檢測",
    version="4.0.0"
)

# 靜態文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ==================== Pydantic Models ====================

class BatchSummary(BaseModel):
    batch_id: int
    test_date: datetime
    total_domains: int
    clean_count: int
    blocked_count: int
    timeout_count: int
    warning_count: int
    partial_count: int
    api_error_count: int
    duration_seconds: Optional[float]
    is_scheduled: bool
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class DomainResultDetail(BaseModel):
    result_id: int
    domain: str
    overall_status: str
    test_date: datetime
    nodes: List[dict]
    
    class Config:
        from_attributes = True


class StatusClassification(BaseModel):
    """狀態分類說明"""
    status: str
    count: int
    percentage: float
    description: str
    domains: List[str]


class DashboardStats(BaseModel):
    """Dashboard 統計數據"""
    total_domains: int
    last_check_time: Optional[datetime]
    next_check_time: Optional[datetime]
    normal_count: int
    abnormal_count: int
    normal_percentage: float
    classifications: List[StatusClassification]


# ==================== Startup/Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化"""
    init_db()
    start_scheduler()
    print("🚀 GlobalpingChecker V4 已啟動")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時清理"""
    stop_scheduler()
    print("👋 GlobalpingChecker V4 已關閉")


# ==================== API Routes ====================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """主頁面 - Dashboard"""
    # 獲取最新批次
    latest_batch = db.query(TestBatch).order_by(desc(TestBatch.test_date)).first()
    
    # 獲取統計數據
    stats = get_dashboard_stats(db, latest_batch)
    
    # 轉換為字典以便 JSON 序列化
    stats_dict = stats.model_dump()
    
    # 處理 datetime 序列化
    if stats_dict.get("last_check_time"):
        stats_dict["last_check_time"] = stats_dict["last_check_time"].isoformat()
    if stats_dict.get("next_check_time"):
        stats_dict["next_check_time"] = stats_dict["next_check_time"].isoformat()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats_dict,
        "latest_batch": latest_batch
    })


@app.get("/api/stats", response_model=DashboardStats)
async def get_stats(db: Session = Depends(get_db)):
    """獲取 Dashboard 統計數據"""
    latest_batch = db.query(TestBatch).order_by(desc(TestBatch.test_date)).first()
    return get_dashboard_stats(db, latest_batch)


@app.get("/api/batches", response_model=List[BatchSummary])
async def list_batches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """列出所有測試批次"""
    batches = db.query(TestBatch).order_by(
        desc(TestBatch.test_date)
    ).offset(offset).limit(limit).all()
    return batches


@app.get("/api/batches/{batch_id}", response_model=BatchSummary)
async def get_batch(batch_id: int, db: Session = Depends(get_db)):
    """獲取特定批次詳情"""
    batch = db.query(TestBatch).filter(TestBatch.batch_id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@app.get("/api/batches/{batch_id}/results")
async def get_batch_results(
    batch_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """獲取批次的域名結果"""
    query = db.query(DomainResult).filter(DomainResult.batch_id == batch_id)
    
    if status:
        query = query.filter(DomainResult.overall_status == status)
    
    results = query.order_by(DomainResult.domain).all()
    
    # 附加節點詳情
    output = []
    for r in results:
        nodes = db.query(NodeDetail).filter(NodeDetail.result_id == r.result_id).all()
        output.append({
            "result_id": r.result_id,
            "domain": r.domain,
            "overall_status": r.overall_status,
            "test_date": r.test_date.isoformat(),
            "nodes": [
                {
                    "isp": n.node_isp,
                    "asn": n.node_asn,
                    "city": n.node_city,
                    "node_ip": n.node_ip,
                    "target_ip": n.target_ip,
                    "status": n.status,
                    "http_code": n.http_code,
                    "response_time_ms": n.response_time_ms
                }
                for n in nodes
            ]
        })
    
    return output


@app.get("/api/batches/{batch_id}/classification")
async def get_batch_classification(batch_id: int, db: Session = Depends(get_db)):
    """獲取批次的分類結果"""
    batch = db.query(TestBatch).filter(TestBatch.batch_id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return get_classification_details(db, batch_id, batch.total_domains)


@app.get("/api/domains/{domain}")
async def get_domain_history(
    domain: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """獲取域名的歷史記錄"""
    results = db.query(DomainResult).filter(
        DomainResult.domain == domain
    ).order_by(desc(DomainResult.test_date)).limit(limit).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    output = []
    for r in results:
        nodes = db.query(NodeDetail).filter(NodeDetail.result_id == r.result_id).all()
        output.append({
            "batch_id": r.batch_id,
            "domain": r.domain,
            "overall_status": r.overall_status,
            "test_date": r.test_date.isoformat(),
            "nodes": [
                {
                    "isp": n.node_isp,
                    "asn": n.node_asn,
                    "city": n.node_city,
                    "node_ip": n.node_ip,
                    "target_ip": n.target_ip,
                    "status": n.status,
                    "http_code": n.http_code
                }
                for n in nodes
            ]
        })
    
    return output


@app.get("/api/history/changes")
async def get_status_changes(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """獲取狀態變化記錄"""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    changes = db.query(DomainHistory).filter(
        DomainHistory.changed_at >= since
    ).order_by(desc(DomainHistory.changed_at)).all()
    
    return [
        {
            "domain": c.domain,
            "previous_status": c.previous_status,
            "current_status": c.current_status,
            "changed_at": c.changed_at.isoformat(),
            "batch_id": c.batch_id,
            "notes": c.notes
        }
        for c in changes
    ]


@app.get("/api/scheduler/logs")
async def get_scheduler_logs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """獲取排程執行日誌"""
    logs = db.query(SchedulerLog).order_by(
        desc(SchedulerLog.run_time)
    ).limit(limit).all()
    
    return [
        {
            "log_id": l.log_id,
            "run_time": l.run_time.isoformat(),
            "batch_id": l.batch_id,
            "status": l.status,
            "domains_checked": l.domains_checked,
            "duration_seconds": l.duration_seconds,
            "error_message": l.error_message
        }
        for l in logs
    ]


@app.post("/api/check/trigger")
async def trigger_check():
    """手動觸發檢測"""
    import asyncio
    asyncio.create_task(run_once())
    return {"message": "檢測任務已加入佇列", "status": "queued"}


# ==================== Helper Functions ====================

def get_dashboard_stats(db: Session, latest_batch: Optional[TestBatch]) -> DashboardStats:
    """計算 Dashboard 統計數據"""
    if not latest_batch:
        return DashboardStats(
            total_domains=0,
            last_check_time=None,
            next_check_time=None,
            normal_count=0,
            abnormal_count=0,
            normal_percentage=0.0,
            classifications=[]
        )
    
    total = latest_batch.total_domains
    normal = latest_batch.clean_count
    abnormal = total - normal
    
    # 計算下次檢測時間
    interval = settings.check_interval_minutes
    next_check = latest_batch.test_date + timedelta(minutes=interval)
    
    # 獲取分類詳情
    classifications = get_classification_details(db, latest_batch.batch_id, total)
    
    return DashboardStats(
        total_domains=total,
        last_check_time=latest_batch.test_date,
        next_check_time=next_check,
        normal_count=normal,
        abnormal_count=abnormal,
        normal_percentage=round(normal / total * 100, 1) if total > 0 else 0.0,
        classifications=classifications
    )


def get_classification_details(db: Session, batch_id: int, total: int) -> List[StatusClassification]:
    """獲取狀態分類詳情"""
    status_info = {
        "CLEAN": {
            "description": "正常連通 - 所有節點都能正常訪問，HTTP 回應 2xx/3xx",
            "emoji": "✅"
        },
        "BLOCKED": {
            "description": "DNS 污染 - 解析到已知的封鎖 IP（如 36.86.63.185）",
            "emoji": "🚨"
        },
        "TIMEOUT": {
            "description": "完全超時 - 所有節點都無法連接或無回應",
            "emoji": "⏱️"
        },
        "WARNING": {
            "description": "服務異常 - HTTP 回應非正常狀態碼（4xx/5xx）",
            "emoji": "⚠️"
        },
        "PARTIAL": {
            "description": "部分異常 - 部分節點正常，部分節點異常",
            "emoji": "🔄"
        },
        "API_ERROR": {
            "description": "檢測失敗 - API 請求錯誤或超時",
            "emoji": "❌"
        }
    }
    
    classifications = []
    
    for status, info in status_info.items():
        results = db.query(DomainResult).filter(
            DomainResult.batch_id == batch_id,
            DomainResult.overall_status == status
        ).all()
        
        count = len(results)
        if count > 0 or status in ["CLEAN", "BLOCKED"]:  # 總是顯示 CLEAN 和 BLOCKED
            classifications.append(StatusClassification(
                status=f"{info['emoji']} {status}",
                count=count,
                percentage=round(count / total * 100, 1) if total > 0 else 0.0,
                description=info["description"],
                domains=[r.domain for r in results]
            ))
    
    return classifications


# ==================== CLI Entry Point ====================

def run_server():
    """啟動 Web 服務器"""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )


if __name__ == "__main__":
    run_server()
