"""
GlobalpingChecker V5 - FastAPI Application

變更自 V4.1：
- 新增 /api/alerts 端點（Telegram 告警歷史）
- 新增 /api/quota 端點（即時 API 額度查詢）
- 版本號更新為 5.0.0
- Domain 新增 primary_country 欄位
- TestBatch 新增 api_calls_used 欄位
"""
import asyncio
from datetime import datetime
from typing import Optional
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
    TestBatch, CheckCycle, CycleType, DomainZoneHistory,
    SystemLog, Alert, AlertType, NodePool
)

settings = get_settings()

live_status = {
    "is_checking": False,
    "current_domain": None,
    "progress": 0,
    "total": 0,
    "cycle_type": None,
    "started_at": None,
    "log": [],
}

app = FastAPI(
    title="GlobalpingChecker V5",
    description="智能循環檢測系統 V5 - 多國家 DNS 監控",
    version="5.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

scheduler = None


# ==================== Startup / Shutdown ====================

@app.on_event("startup")
async def startup_event():
    global scheduler
    init_db()

    db = SessionLocal()
    try:
        from .zone_manager import ZoneManager
        zm = ZoneManager(db)
        with open(settings.domains_file, 'r', encoding='utf-8') as f:
            domains = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        stats = zm.initialize_domains(domains)
        print(f"📋 域名初始化: 新增 {stats['added']} | 已存在 {stats['existing']}")
    finally:
        db.close()

    from .node_pool import NodePoolManager
    async def _init_pool():
        try:
            npm = NodePoolManager()
            pool_stats = npm.get_node_pool_stats()
            total = sum(v.get("total", 0) for v in pool_stats.values())
            if total == 0:
                print("📡 節點池為空，開始初始化...")
                await npm.initialize_node_pool()
            else:
                print(f"📡 節點池已有資料: {pool_stats}")
        except Exception as e:
            print(f"⚠️  節點池初始化失敗: {e}")
    asyncio.create_task(_init_pool())

    async def _scheduled_refresh():
        import asyncio as _a
        from datetime import timedelta
        while True:
            now = datetime.now()
            nxt = now.replace(hour=settings.node_pool_refresh_hour, minute=0, second=0, microsecond=0)
            if nxt <= now:
                nxt += timedelta(days=1)
            await _a.sleep((nxt - now).total_seconds())
            try:
                npm = NodePoolManager()
                await npm.refresh_node_pool()
                print("📡 節點池已定期刷新")
            except Exception as e:
                print(f"⚠️  節點池刷新失敗: {e}")
    asyncio.create_task(_scheduled_refresh())

    from .cycle_scheduler import CycleScheduler
    from .checker import run_cycle_check
    scheduler = CycleScheduler(SessionLocal)
    scheduler.daily_reset_hour   = settings.normal_zone_reset_hour
    scheduler.daily_reset_minute = 1
    scheduler.set_check_callback(run_cycle_check)
    scheduler.start()

    countries = ", ".join(
        f"{c} ({n})" for c, n in zip(
            settings.target_country_list, settings.target_country_name_list)
    )
    print(f"🌏 檢測國家: {countries}")
    print("🚀 GlobalpingChecker V5 已啟動")


@app.on_event("shutdown")
async def shutdown_event():
    global scheduler
    if scheduler:
        scheduler.stop()
    print("👋 GlobalpingChecker V5 已關閉")


# ==================== Web Pages ====================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    from .zone_manager import ZoneManager
    zm         = ZoneManager(db)
    zone_stats = zm.get_zone_stats()
    latest     = db.query(TestBatch).order_by(desc(TestBatch.test_date)).first()
    cycle_info = scheduler.get_current_cycle_info() if scheduler else {}
    stats = {
        "zone_stats":      zone_stats,
        "total_domains":   sum(zone_stats.values()),
        "normal_count":    zone_stats.get("NORMAL", 0),
        "abnormal_count":  zone_stats.get("ABNORMAL", 0),
        "pending_count":   zone_stats.get("PENDING", 0),
        "cycle_info":      cycle_info,
        "last_check_time": latest.test_date.isoformat() if latest else None,
        "version":         "5.0.0",
    }
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "stats": stats,
        "latest_batch": latest, "cycle_info": cycle_info,
    })


# ==================== Core API ====================

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    from .zone_manager import ZoneManager
    zm         = ZoneManager(db)
    zone_stats = zm.get_zone_stats()
    latest     = db.query(TestBatch).order_by(desc(TestBatch.test_date)).first()
    cycle_info = scheduler.get_current_cycle_info() if scheduler else {}
    return {
        "version":         "5.0.0",
        "zone_stats":      zone_stats,
        "total_domains":   sum(zone_stats.values()),
        "normal_count":    zone_stats.get("NORMAL", 0),
        "abnormal_count":  zone_stats.get("ABNORMAL", 0),
        "pending_count":   zone_stats.get("PENDING", 0),
        "last_check_time": latest.test_date.isoformat() if latest else None,
        "cycle_info":      cycle_info,
    }


@app.get("/api/live")
async def get_live_status():
    return live_status


@app.get("/api/progress")
async def get_progress():
    from .checker import _check_progress
    return _check_progress


@app.get("/api/recent-results")
async def get_recent_results(
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    從資料庫撈最近一批次的檢測結果，供 Dashboard 常態顯示。
    回傳格式與 _check_progress["recent_results"] 相同，前端可直接複用。
    """
    from .node_pool import _isp_priority

    def _get_top(isp):
        if not isp:
            return None
        rank = _isp_priority(isp)
        return f"TOP{rank}" if rank <= 30 else None

    # 取最新一批次的 batch_id
    latest_batch = db.query(TestBatch).order_by(desc(TestBatch.test_date)).first()
    if not latest_batch:
        return {"results": [], "batch_id": None, "batch_date": None}

    # 撈該批次的所有結果
    results = (
        db.query(DomainResult)
        .filter(DomainResult.batch_id == latest_batch.batch_id)
        .order_by(desc(DomainResult.test_date))
        .limit(limit)
        .all()
    )

    items = []
    for r in results:
        # 取節點詳情
        node_rows = (
            db.query(NodeDetail)
            .filter(NodeDetail.result_id == r.result_id)
            .all()
        )
        # 依 isp_rank 排序
        node_rows_sorted = sorted(
            node_rows,
            key=lambda n: _isp_priority(n.node_isp or "")
        )
        node_summaries = [
            {
                "isp":    n.node_isp,
                "city":   n.node_city,
                "status": n.status.value if n.status else "",
                "top":    _get_top(n.node_isp),
            }
            for n in node_rows_sorted[:5]
        ]
        first_node = node_rows_sorted[0] if node_rows_sorted else None
        items.append({
            "domain":    r.domain,
            "status":    r.overall_status.value if r.overall_status else "",
            "error":     r.error_message or "",
            "time":      r.test_date.isoformat() + "Z",
            "dur_ms":    r.check_duration_ms,
            "isp":       first_node.node_isp if first_node else None,
            "city":      first_node.node_city if first_node else None,
            "top":       _get_top(first_node.node_isp) if first_node else None,
            "type":      "dns",
            "http_code": first_node.http_code if first_node else None,
            "nodes":     node_summaries,
        })

    return {
        "results":    items,
        "batch_id":   latest_batch.batch_id,
        "batch_date": latest_batch.test_date.isoformat() + "Z",
        "total":      len(items),
    }


@app.get("/api/cycle")
async def get_cycle():
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    return scheduler.get_current_cycle_info()


@app.get("/api/schedule")
async def get_schedule():
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    return scheduler.get_schedule_info()


@app.post("/api/check/stop")
async def stop_check():
    """暫停當前正在進行的檢測（完成當前域名後停止）"""
    from .checker import _check_progress
    import app.checker as checker_mod
    if not _check_progress.get("running"):
        return {"message": "目前沒有正在進行的檢測", "status": "idle"}
    checker_mod._stop_flag = True
    return {"message": "暫停指令已送出，將在當前域名完成後停止", "status": "stopping"}


@app.post("/api/check/recheck-abnormal")
async def recheck_abnormal():
    """暫停當前檢測，重新只檢測異常區域名，完成後自動繼續正常區（PENDING）"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    import app.checker as checker_mod
    from .checker import _check_progress, run_cycle_check
    from .models import DomainZone, CycleType
    from .zone_manager import ZoneManager

    # 若有進行中的檢測，先設旗標暫停
    if _check_progress.get("running"):
        checker_mod._stop_flag = True
        await asyncio.sleep(2)

    # 撈異常區域名
    db = SessionLocal()
    try:
        zm = ZoneManager(db)
        abnormal_domains = zm.get_domain_names_by_zone(DomainZone.ABNORMAL)
        pending_domains  = zm.get_domain_names_by_zone(DomainZone.PENDING)
    finally:
        db.close()

    if not abnormal_domains:
        return {"message": "異常區目前沒有域名", "status": "empty", "count": 0}

    cycle_id = scheduler.current_cycle_id

    async def _run_abnormal_then_pending():
        """先跑異常區，完成後自動繼續 PENDING，最後輪詢 NORMAL 區"""
        print(f"\n🔁 重檢異常區 ({len(abnormal_domains)} 個)，完成後繼續 PENDING ({len(pending_domains)} 個)")
        await run_cycle_check(
            domains    = abnormal_domains,
            cycle_id   = cycle_id,
            cycle_type = CycleType.ABNORMAL_CHECK,
            iteration  = 1,
        )
        # 重新撈最新的 PENDING（異常區跑完後可能有新增）
        db2 = SessionLocal()
        try:
            zm2 = ZoneManager(db2)
            remaining_pending = zm2.get_domain_names_by_zone(DomainZone.PENDING)
        finally:
            db2.close()
        if remaining_pending:
            print(f"\n▶️  自動繼續正常區檢測 ({len(remaining_pending)} 個 PENDING 域名)")
            await run_cycle_check(
                domains    = remaining_pending,
                cycle_id   = cycle_id,
                cycle_type = CycleType.ABNORMAL_CHECK,
                iteration  = 2,
            )
        else:
            print("\n✅ 無 PENDING 域名，全部完成")

        # NORMAL 區輪詢：確認已知正常域名是否被封鎖
        import app.checker as checker_mod
        iteration = 3
        while True:
            if checker_mod._stop_flag:
                print("⏹️  NORMAL 區輪詢已暫停")
                checker_mod._stop_flag = False
                break
            db3 = SessionLocal()
            try:
                zm3 = ZoneManager(db3)
                normal_domains = zm3.get_domain_names_by_zone(DomainZone.NORMAL)
            finally:
                db3.close()
            if not normal_domains:
                print("\n✅ 無 NORMAL 域名需要輪詢，結束")
                break
            print(f"\n🔄 輪詢正常區 ({len(normal_domains)} 個，第 {iteration-2} 輪)")
            await run_cycle_check(
                domains    = normal_domains,
                cycle_id   = cycle_id,
                cycle_type = CycleType.ABNORMAL_CHECK,
                iteration  = iteration,
            )
            iteration += 1
            # 每輪結束後休息 5 分鐘再繼續
            print(f"\n⏸️  NORMAL 區輪詢休息 5 分鐘...")
            for _ in range(300):  # 300 秒，每秒檢查一次停止旗標
                if checker_mod._stop_flag:
                    break
                await asyncio.sleep(1)

    asyncio.create_task(_run_abnormal_then_pending())
    return {
        "message": f"重新檢測異常區 {len(abnormal_domains)} 個域名，完成後自動繼續 {len(pending_domains)} 個 PENDING",
        "status": "queued",
        "abnormal_count": len(abnormal_domains),
        "pending_count":  len(pending_domains),
    }


@app.post("/api/check/trigger")
async def trigger_check():
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    asyncio.create_task(scheduler.trigger_check())
    return {"message": "檢測任務已加入佇列", "status": "queued"}


# ==================== V5 新增 API ====================

@app.get("/api/quota")
async def get_api_quota():
    """查詢 Globalping API 剩餘額度（V5 新增）"""
    import httpx
    headers = {"Authorization": f"Bearer {settings.globalping_token}"}
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{settings.globalping_api_url}/limits",
                headers=headers, timeout=10.0
            )
            if r.status_code == 200:
                data = r.json()
                remaining = (
                    data.get('rateLimit', {})
                    .get('measurements', {})
                    .get('create', {})
                    .get('remaining', 0)
                )
                return {
                    "remaining":  remaining,
                    "warning":    remaining < settings.api_quota_warning_threshold,
                    "threshold":  settings.api_quota_warning_threshold,
                    "raw":        data,
                }
            return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/alerts")
async def get_alerts(
    limit: int = Query(50, ge=1, le=200),
    alert_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """取得 Telegram 告警歷史（V5 新增）"""
    q = db.query(Alert)
    if alert_type:
        q = q.filter(Alert.alert_type == alert_type)
    alerts = q.order_by(desc(Alert.created_at)).limit(limit).all()
    return [
        {
            "alert_id":   a.alert_id,
            "alert_type": a.alert_type.value,
            "message":    a.message,
            "details":    a.details,
            "sent_ok":    a.sent_ok,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


# ==================== Domains API ====================

@app.get("/api/zones/{zone}")
async def get_zone_domains(
    zone: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    try:
        zone_enum = DomainZone(zone.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid zone: {zone}")
    domains = (
        db.query(Domain)
        .filter(Domain.zone == zone_enum)
        .order_by(Domain.domain)
        .offset(offset).limit(limit).all()
    )
    total = db.query(func.count(Domain.domain_id)).filter(Domain.zone == zone_enum).scalar()
    return {
        "zone":  zone_enum.value,
        "total": total,
        "domains": [
            {
                "domain":               d.domain,
                "current_status":       d.current_status.value if d.current_status else None,
                "last_check_time":      d.last_check_time.isoformat() if d.last_check_time else None,
                "consecutive_normal":   d.consecutive_normal,
                "consecutive_abnormal": d.consecutive_abnormal,
                "total_checks":         d.total_checks,
                "primary_country":      d.primary_country,
            }
            for d in domains
        ],
    }


@app.get("/api/domains/{domain}")
async def get_domain_history(
    domain: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    rec = db.query(Domain).filter(Domain.domain == domain).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Domain not found")
    results = (
        db.query(DomainResult)
        .filter(DomainResult.domain == domain)
        .order_by(desc(DomainResult.test_date)).limit(limit).all()
    )
    zone_hist = (
        db.query(DomainZoneHistory)
        .filter(DomainZoneHistory.domain_id == rec.domain_id)
        .order_by(desc(DomainZoneHistory.changed_at)).limit(10).all()
    )

    # 預先查出所有 result_id 對應的 node_details，並一次查出 ISP rank
    def _get_node_details(result_id):
        nds = db.query(NodeDetail).filter(NodeDetail.result_id == result_id).all()
        details = []
        for nd in nds:
            isp_rank = None
            if nd.node_isp:
                row = (
                    db.query(NodePool.isp_rank)
                    .filter(NodePool.isp == nd.node_isp)
                    .first()
                )
                isp_rank = row[0] if row else None
            details.append({
                "isp":      nd.node_isp,
                "city":     nd.node_city,
                "country":  nd.node_country,
                "status":   nd.status.value if nd.status else None,
                "target_ip": nd.target_ip,
                "response_time_ms": nd.response_time_ms,
                "asn":      nd.node_asn,
                "isp_rank": isp_rank,
            })
        return details
    return {
        "domain":               domain,
        "current_zone":         rec.zone.value,
        "current_status":       rec.current_status.value if rec.current_status else None,
        "consecutive_normal":   rec.consecutive_normal,
        "consecutive_abnormal": rec.consecutive_abnormal,
        "total_checks":         rec.total_checks,
        "primary_country":      rec.primary_country,
        "check_history": [
            {
                "batch_id":      r.batch_id,
                "status":        r.overall_status.value if r.overall_status else None,
                "zone_changed":  r.zone_changed,
                "previous_zone": r.previous_zone.value if r.previous_zone else None,
                "new_zone":      r.new_zone.value if r.new_zone else None,
                "error_message": r.error_message,
                "test_date":     r.test_date.isoformat(),
                "duration_ms":   r.check_duration_ms,
                "node_details":  _get_node_details(r.result_id),
            }
            for r in results
        ],
        "zone_history": [
            {
                "previous_zone": h.previous_zone.value if h.previous_zone else None,
                "new_zone":      h.new_zone.value,
                "reason":        h.reason,
                "changed_at":    h.changed_at.isoformat(),
            }
            for h in zone_hist
        ],
    }


# ==================== Batches API ====================

@app.get("/api/batches")
async def list_batches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    batches = (
        db.query(TestBatch)
        .order_by(desc(TestBatch.test_date))
        .offset(offset).limit(limit).all()
    )
    return [
        {
            "batch_id":          b.batch_id,
            "cycle_type":        b.cycle_type.value if b.cycle_type else None,
            "iteration":         b.iteration,
            "test_date":         b.test_date.isoformat(),
            "total_domains":     b.total_domains,
            "clean_count":       b.clean_count,
            "blocked_count":     b.blocked_count,
            "timeout_count":     b.timeout_count,
            "warning_count":     b.warning_count,
            "partial_count":     b.partial_count,
            "api_error_count":   b.api_error_count,
            "moved_to_normal":   b.moved_to_normal,
            "moved_to_abnormal": b.moved_to_abnormal,
            "duration_seconds":  b.duration_seconds,
            "api_calls_used":    b.api_calls_used,
            "notes":             b.notes,
        }
        for b in batches
    ]


@app.get("/api/logs")
async def get_logs(
    limit: int = Query(50, ge=1, le=200),
    log_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(SystemLog)
    if log_type:
        q = q.filter(SystemLog.log_type == log_type)
    logs = q.order_by(desc(SystemLog.log_time)).limit(limit).all()
    return [
        {
            "log_id":   l.log_id,
            "log_type": l.log_type,
            "message":  l.message,
            "details":  l.details,
            "log_time": l.log_time.isoformat(),
        }
        for l in logs
    ]


# ==================== Nodes API ====================

@app.get("/api/nodes/pool")
async def get_node_pool(db: Session = Depends(get_db)):
    nodes = (
        db.query(NodePool)
        .filter(NodePool.is_active == True)
        .order_by(NodePool.isp_rank, NodePool.city).all()
    )
    return {
        "total_nodes": len(nodes),
        "nodes": [
            {
                "node_id":      n.node_id,
                "node_ip":      n.node_ip,
                "country":      n.country,
                "country_name": n.country_name,
                "city":         n.city,
                "isp":          n.isp,
                "asn":          n.asn,
                "isp_rank":     n.isp_rank,
                "is_top_isp":   n.is_top_isp,
                "last_verified": n.last_verified.isoformat() if n.last_verified else None,
            }
            for n in nodes
        ],
    }


@app.post("/api/nodes/pool/refresh")
async def refresh_node_pool():
    from .node_pool import NodePoolManager
    npm = NodePoolManager()
    asyncio.create_task(npm.refresh_node_pool())
    return {"message": "節點池刷新任務已啟動", "status": "started"}


@app.post("/api/domains/reset-to-pending")
async def reset_domains_to_pending():
    """將所有異常區域名重置為待分類（V5）"""
    db = SessionLocal()
    try:
        updated = db.query(Domain).filter(Domain.zone == DomainZone.ABNORMAL).update(
            {"zone": DomainZone.PENDING, "consecutive_abnormal": 0}
        )
        db.commit()
        return {"message": f"已重置 {updated} 個異常區域名為待分類", "updated": updated}
    finally:
        db.close()


@app.post("/api/domains/reload")
async def reload_domains():
    db = SessionLocal()
    try:
        from .zone_manager import ZoneManager
        zm = ZoneManager(db)
        with open(settings.domains_file, 'r', encoding='utf-8') as f:
            domains = [l.strip() for l in f if l.strip() and not l.startswith('#')]
        stats = zm.initialize_domains(domains)
        return {"message": f"已重新加載 {len(domains)} 個域名", **stats, "total": len(domains)}
    finally:
        db.close()
