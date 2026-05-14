"""
GlobalpingChecker V4.1 - FastAPI Web Application
智能循環檢測系統 - Web Dashboard 和 API
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from .config import get_settings
from .database import get_db, init_db, SessionLocal
from .models import (
    Domain, DomainZone, DomainStatus, DomainResult, NodeDetail,
    TestBatch, CheckCycle, CycleType, DomainZoneHistory, SystemLog
)
from .zone_manager import ZoneManager
from .cycle_scheduler import CycleScheduler
from .checker import run_cycle_check
from .node_validator import NodeValidator, validate_single_ip

settings = get_settings()

# ==================== 即時檢測狀態 ====================
live_status = {
    "is_checking": False,
    "current_domain": None,
    "current_node_brand": None,
    "current_node_top": None,
    "current_node_city": None,
    "current_node_isp": None,
    "progress": 0,
    "total": 0,
    "cycle_type": None,
    "started_at": None,
    "log": [],           # 最近 50 筆即時 log
}

app = FastAPI(
    title="GlobalpingChecker V4.1",
    description="智能循環檢測系統 - 印尼 ISP DNS 監控",
    version="4.1.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 全局排程器
scheduler: Optional[CycleScheduler] = None


# ==================== Startup/Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """應用啟動"""
    global scheduler
    
    init_db()
    
    # 初始化域名列表
    db = SessionLocal()
    try:
        zone_manager = ZoneManager(db)
        with open(settings.domains_file, 'r', encoding='utf-8') as f:
            domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        stats = zone_manager.initialize_domains(domains)
        print(f"📋 域名初始化: 新增 {stats['added']} 個, 已存在 {stats['existing']} 個")
    finally:
        db.close()
    
    # 初始化節點池（異步任務）
    from .node_pool import NodePoolManager
    import asyncio
    
    async def init_node_pool():
        try:
            node_pool = NodePoolManager()
            # 只在節點池為空時才初始化（避免每次重啟都重新驗證全部節點）
            stats = node_pool.get_node_pool_stats()
            total = sum(v.get("total", 0) for v in stats.values())
            if total == 0:
                print("📡 節點池為空，開始初始化...")
                await node_pool.initialize_node_pool()
            else:
                print(f"📡 節點池已有資料，跳過初始化: {stats}")
            pool_stats = node_pool.get_node_pool_stats()
            print(f"📡 節點池統計: {pool_stats}")
        except Exception as e:
            print(f"⚠️  節點池初始化失敗: {e}")
    
    # 在後台初始化節點池
    asyncio.create_task(init_node_pool())
    
    # 每天凌晨 3:00 自動刷新節點池
    async def scheduled_node_pool_refresh():
        import asyncio as _asyncio
        while True:
            now = datetime.now()
            # 計算距離下一個凌晨 3:00 的秒數
            next_refresh = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if next_refresh <= now:
                from datetime import timedelta
                next_refresh += timedelta(days=1)
            wait_seconds = (next_refresh - now).total_seconds()
            print(f"📡 節點池下次刷新: {next_refresh.strftime('%Y-%m-%d %H:%M')} (約 {wait_seconds/3600:.1f} 小時後)")
            await _asyncio.sleep(wait_seconds)
            try:
                node_pool = NodePoolManager()
                await node_pool.refresh_node_pool()
            except Exception as e:
                print(f"⚠️  節點池定期刷新失敗: {e}")
    
    asyncio.create_task(scheduled_node_pool_refresh())
    
    # 啟動排程器
    scheduler = CycleScheduler(SessionLocal)
    scheduler.abnormal_check_hour = settings.abnormal_check_hour
    scheduler.normal_check_hour = settings.normal_check_hour
    scheduler.check_interval = settings.check_interval_minutes
    scheduler.max_iterations = settings.max_iterations
    scheduler.set_check_callback(run_cycle_check)
    scheduler.start()
    
    # 顯示啟用的檢測國家
    enabled_countries = settings.target_country_list
    enabled_names = settings.target_country_name_list
    countries_info = ", ".join([f"{code} ({name})" for code, name in zip(enabled_countries, enabled_names)])
    print(f"🌏 檢測國家: {countries_info}")
    print("🚀 GlobalpingChecker V4.1 已啟動")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉"""
    global scheduler
    if scheduler:
        scheduler.stop()
    print("👋 GlobalpingChecker V4.1 已關閉")


# ==================== Web Pages ====================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """主頁面 - Dashboard"""
    # 獲取區域統計
    zone_manager = ZoneManager(db)
    zone_stats = zone_manager.get_zone_stats()
    
    # 獲取最新批次
    latest_batch = db.query(TestBatch).order_by(desc(TestBatch.test_date)).first()
    
    # 獲取循環信息
    cycle_info = scheduler.get_current_cycle_info() if scheduler else {}
    
    stats = {
        "zone_stats": zone_stats,
        "total_domains": sum(zone_stats.values()),
        "normal_count": zone_stats.get("NORMAL", 0),
        "abnormal_count": zone_stats.get("ABNORMAL", 0),
        "pending_count": zone_stats.get("PENDING", 0),
        "cycle_info": cycle_info,
        "last_check_time": latest_batch.test_date.isoformat() if latest_batch else None,
    }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "latest_batch": latest_batch,
        "cycle_info": cycle_info
    })


# ==================== API Routes ====================

@app.get("/api/live")
async def get_live_status():
    """取得即時檢測狀態"""
    return live_status


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """獲取統計數據"""
    zone_manager = ZoneManager(db)
    zone_stats = zone_manager.get_zone_stats()
    
    latest_batch = db.query(TestBatch).order_by(desc(TestBatch.test_date)).first()
    cycle_info = scheduler.get_current_cycle_info() if scheduler else {}
    
    return {
        "zone_stats": zone_stats,
        "total_domains": sum(zone_stats.values()),
        "normal_count": zone_stats.get("NORMAL", 0),
        "abnormal_count": zone_stats.get("ABNORMAL", 0),
        "pending_count": zone_stats.get("PENDING", 0),
        "last_check_time": latest_batch.test_date.isoformat() if latest_batch else None,
        "cycle_info": cycle_info
    }


@app.get("/api/cycle")
async def get_cycle_info():
    """獲取當前循環信息"""
    if not scheduler:
        return {"error": "Scheduler not initialized"}
    return scheduler.get_current_cycle_info()


@app.get("/api/progress")
async def get_check_progress():
    """獲取即時檢測進度（輪詢用）"""
    from .checker import _check_progress
    return _check_progress


@app.get("/api/schedule")
async def get_schedule_info():
    """獲取排程配置"""
    if not scheduler:
        return {"error": "Scheduler not initialized"}
    return scheduler.get_schedule_info()


@app.post("/api/check/trigger")
async def trigger_check():
    """手動觸發檢測"""
    if not scheduler:
        return {"error": "Scheduler not initialized"}
    
    asyncio.create_task(scheduler.trigger_check())
    return {"message": "檢測任務已加入佇列", "status": "queued"}


@app.post("/api/domains/reload")
async def reload_domains():
    """重新加载所有域名"""
    db = SessionLocal()
    try:
        zone_manager = ZoneManager(db)
        with open(settings.domains_file, 'r', encoding='utf-8') as f:
            domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        stats = zone_manager.initialize_domains(domains)
        return {
            "message": f"已重新加载 {len(domains)} 个域名",
            "added": stats['added'],
            "existing": stats['existing'],
            "total": len(domains)
        }
    finally:
        db.close()


@app.post("/api/domains/reset-to-pending")
async def reset_domains_to_pending():
    """將所有異常區域名重置為待分類"""
    db = SessionLocal()
    try:
        from .models import Domain, DomainZone
        updated = db.query(Domain).filter(
            Domain.zone == DomainZone.ABNORMAL
        ).update({"zone": DomainZone.PENDING, "consecutive_abnormal": 0})
        db.commit()
        return {"message": f"已重置 {updated} 個域名回待分類", "updated": updated}
    finally:
        db.close()


@app.get("/api/zones/{zone}")
async def get_zone_domains(
    zone: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """獲取指定區域的域名"""
    try:
        zone_enum = DomainZone(zone.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid zone: {zone}")
    
    domains = db.query(Domain).filter(
        Domain.zone == zone_enum
    ).order_by(Domain.domain).offset(offset).limit(limit).all()
    
    total = db.query(func.count(Domain.domain_id)).filter(
        Domain.zone == zone_enum
    ).scalar()
    
    return {
        "zone": zone_enum.value,
        "total": total,
        "domains": [
            {
                "domain": d.domain,
                "current_status": d.current_status.value if d.current_status else None,
                "last_check_time": d.last_check_time.isoformat() if d.last_check_time else None,
                "consecutive_normal": d.consecutive_normal,
                "consecutive_abnormal": d.consecutive_abnormal,
                "total_checks": d.total_checks
            }
            for d in domains
        ]
    }


@app.get("/api/batches")
async def list_batches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """列出所有測試批次"""
    batches = db.query(TestBatch).order_by(
        desc(TestBatch.test_date)
    ).offset(offset).limit(limit).all()
    
    return [
        {
            "batch_id": b.batch_id,
            "cycle_type": b.cycle_type.value if b.cycle_type else None,
            "iteration": b.iteration,
            "test_date": b.test_date.isoformat(),
            "total_domains": b.total_domains,
            "clean_count": b.clean_count,
            "blocked_count": b.blocked_count,
            "timeout_count": b.timeout_count,
            "warning_count": b.warning_count,
            "partial_count": b.partial_count,
            "api_error_count": b.api_error_count,
            "moved_to_normal": b.moved_to_normal,
            "moved_to_abnormal": b.moved_to_abnormal,
            "duration_seconds": b.duration_seconds,
            "notes": b.notes
        }
        for b in batches
    ]


@app.get("/api/batches/{batch_id}")
async def get_batch(batch_id: int, db: Session = Depends(get_db)):
    """獲取批次詳情"""
    batch = db.query(TestBatch).filter(TestBatch.batch_id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return {
        "batch_id": batch.batch_id,
        "cycle_type": batch.cycle_type.value if batch.cycle_type else None,
        "iteration": batch.iteration,
        "test_date": batch.test_date.isoformat(),
        "total_domains": batch.total_domains,
        "clean_count": batch.clean_count,
        "blocked_count": batch.blocked_count,
        "timeout_count": batch.timeout_count,
        "warning_count": batch.warning_count,
        "partial_count": batch.partial_count,
        "api_error_count": batch.api_error_count,
        "moved_to_normal": batch.moved_to_normal,
        "moved_to_abnormal": batch.moved_to_abnormal,
        "duration_seconds": batch.duration_seconds,
        "notes": batch.notes
    }


@app.get("/api/domains/{domain}")
async def get_domain_history(
    domain: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """獲取域名歷史記錄"""
    domain_record = db.query(Domain).filter(Domain.domain == domain).first()
    if not domain_record:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    results = db.query(DomainResult).filter(
        DomainResult.domain == domain
    ).order_by(desc(DomainResult.test_date)).limit(limit).all()
    
    zone_history = db.query(DomainZoneHistory).filter(
        DomainZoneHistory.domain_id == domain_record.domain_id
    ).order_by(desc(DomainZoneHistory.changed_at)).limit(10).all()
    
    return {
        "domain": domain,
        "current_zone": domain_record.zone.value,
        "current_status": domain_record.current_status.value if domain_record.current_status else None,
        "consecutive_normal": domain_record.consecutive_normal,
        "consecutive_abnormal": domain_record.consecutive_abnormal,
        "total_checks": domain_record.total_checks,
        "check_history": [
            {
                "batch_id": r.batch_id,
                "status": r.overall_status.value if r.overall_status else None,
                "zone_changed": r.zone_changed,
                "error_message": r.error_message,
                "test_date": r.test_date.isoformat()
            }
            for r in results
        ],
        "zone_history": [
            {
                "previous_zone": h.previous_zone.value if h.previous_zone else None,
                "new_zone": h.new_zone.value,
                "reason": h.reason,
                "changed_at": h.changed_at.isoformat()
            }
            for h in zone_history
        ]
    }


@app.get("/api/logs")
async def get_system_logs(
    limit: int = Query(50, ge=1, le=200),
    log_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """獲取系統日誌"""
    query = db.query(SystemLog)
    
    if log_type:
        query = query.filter(SystemLog.log_type == log_type)
    
    logs = query.order_by(desc(SystemLog.log_time)).limit(limit).all()
    
    return [
        {
            "log_id": l.log_id,
            "log_type": l.log_type,
            "message": l.message,
            "details": l.details,
            "log_time": l.log_time.isoformat()
        }
        for l in logs
    ]


# ==================== Node Validation API ====================

@app.get("/api/progress")
async def get_check_progress():
    """獲取即時檢測進度"""
    from .checker import _check_progress
    return _check_progress


@app.get("/api/nodes/validate")
async def validate_ip_endpoint(
    ip: str = Query(..., description="IP address to validate"),
    country: str = Query("ID", description="Expected country code (ISO 3166-1 alpha-2), e.g. ID, VN, TH")
):
    """驗證單個 IP 地址的地理位置"""
    result = await validate_single_ip(ip, expected_country=country)
    return result


@app.get("/api/nodes/pool")
async def get_node_pool(db: Session = Depends(get_db)):
    """獲取節點池信息（依 ISP 優先級排序）"""
    from .node_pool import NodePool, NodePoolManager, _rank_to_brand

    # 依 isp_rank ASC 排序，讓 TOP30 ISP 節點排在前面
    nodes = (
        db.query(NodePool)
        .filter(NodePool.is_active == True)
        .order_by(NodePool.isp_rank, NodePool.city)
        .all()
    )

    pool_manager = NodePoolManager()
    stats = pool_manager.get_node_pool_stats()

    node_list = [
        {
            "node_id":     node.node_id,
            "node_ip":     node.node_ip,
            "country":     node.country,
            "country_name": node.country_name,
            "city":        node.city,
            "isp":         node.isp,
            "asn":         node.asn,
            "isp_rank":    node.isp_rank,
            "isp_brand":   _rank_to_brand(node.isp_rank),
            "last_verified": node.last_verified.isoformat() if node.last_verified else None,
            "created_at":  node.created_at.isoformat() if node.created_at else None,
        }
        for node in nodes
    ]

    return {
        "total_nodes": len(node_list),
        "stats": stats,
        "nodes": node_list,
    }


@app.get("/api/nodes/pool/{country}")
async def get_country_node_pool(country: str, db: Session = Depends(get_db)):
    """獲取指定國家的節點池（依 ISP 優先級排序）"""
    from .node_pool import NodePool, _rank_to_brand

    nodes = (
        db.query(NodePool)
        .filter(NodePool.country == country, NodePool.is_active == True)
        .order_by(NodePool.isp_rank, NodePool.city)
        .all()
    )

    node_list = [
        {
            "node_id":     node.node_id,
            "node_ip":     node.node_ip,
            "country":     node.country,
            "country_name": node.country_name,
            "city":        node.city,
            "isp":         node.isp,
            "asn":         node.asn,
            "isp_rank":    node.isp_rank,
            "isp_brand":   _rank_to_brand(node.isp_rank),
            "last_verified": node.last_verified.isoformat() if node.last_verified else None,
            "created_at":  node.created_at.isoformat() if node.created_at else None,
        }
        for node in nodes
    ]

    return {
        "country": country,
        "total_nodes": len(node_list),
        "nodes": node_list
    }


@app.post("/api/nodes/pool/refresh")
async def refresh_node_pool():
    """手動刷新節點池"""
    from .node_pool import NodePoolManager
    import asyncio
    
    pool_manager = NodePoolManager()
    asyncio.create_task(pool_manager.refresh_node_pool())
    
    return {"message": "節點池刷新任務已啟動", "status": "started"}


@app.get("/api/nodes/validate-batch/{batch_id}")
async def validate_batch_nodes_endpoint(
    batch_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """驗證批次中的所有節點 IP"""
    validator = NodeValidator()
    result = await validator.validate_batch_nodes(db, batch_id, limit)
    return result


@app.get("/api/batches/{batch_id}/results")
async def get_batch_results_v2(
    batch_id: int,
    status: Optional[str] = None,
    zone_changed: Optional[bool] = None,
    domain: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """獲取批次的域名結果（支援域名過濾）"""
    query = db.query(DomainResult).filter(DomainResult.batch_id == batch_id)
    
    if status:
        query = query.filter(DomainResult.overall_status == status)
    
    if zone_changed is not None:
        query = query.filter(DomainResult.zone_changed == zone_changed)
    
    if domain:
        query = query.filter(DomainResult.domain == domain)
    
    results = query.order_by(DomainResult.domain).all()
    
    output = []
    for r in results:
        nodes = db.query(NodeDetail).filter(NodeDetail.result_id == r.result_id).all()
        output.append({
            "result_id": r.result_id,
            "domain": r.domain,
            "overall_status": r.overall_status.value if r.overall_status else None,
            "previous_zone": r.previous_zone.value if r.previous_zone else None,
            "new_zone": r.new_zone.value if r.new_zone else None,
            "zone_changed": r.zone_changed,
            "error_message": r.error_message,
            "test_date": r.test_date.isoformat(),
            "nodes": [
                {
                    "isp": n.node_isp,
                    "asn": n.node_asn,
                    "city": n.node_city,
                    "node_ip": n.node_ip,
                    "target_ip": n.target_ip,
                    "status": n.status.value if n.status else None,
                    "http_code": n.http_code,
                    "response_time_ms": n.response_time_ms
                }
                for n in nodes
            ]
        })
    
    return output
