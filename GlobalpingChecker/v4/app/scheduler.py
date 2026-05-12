"""
GlobalpingChecker V4 - Scheduler
每 90 分鐘自動執行檢測
"""
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from .config import get_settings
from .database import SessionLocal, SchedulerLog, init_db
from .checker import run_check

settings = get_settings()

scheduler = AsyncIOScheduler()


async def scheduled_check():
    """排程檢測任務"""
    db = SessionLocal()
    log = SchedulerLog(
        run_time=datetime.utcnow(),
        status="RUNNING"
    )
    db.add(log)
    db.commit()
    log_id = log.log_id
    
    try:
        print(f"\n{'='*60}")
        print(f"⏰ 排程檢測開始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        start_time = datetime.utcnow()
        
        # 執行檢測
        batch_id = await run_check(
            domains_file=settings.domains_file,
            notes=f"排程自動檢測 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            is_scheduled=True
        )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # 更新日誌
        log = db.query(SchedulerLog).filter(SchedulerLog.log_id == log_id).first()
        if log:
            log.status = "SUCCESS" if batch_id > 0 else "FAILED"
            log.batch_id = batch_id if batch_id > 0 else None
            log.duration_seconds = duration
            db.commit()
        
        print(f"\n✅ 排程檢測完成，耗時 {duration:.1f} 秒")
        
    except Exception as e:
        print(f"\n❌ 排程檢測失敗: {e}")
        log = db.query(SchedulerLog).filter(SchedulerLog.log_id == log_id).first()
        if log:
            log.status = "FAILED"
            log.error_message = str(e)
            db.commit()
    finally:
        db.close()


def start_scheduler():
    """啟動排程器"""
    interval_minutes = settings.check_interval_minutes
    
    scheduler.add_job(
        scheduled_check,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="domain_check",
        name=f"Domain Check (every {interval_minutes} minutes)",
        replace_existing=True
    )
    
    scheduler.start()
    print(f"⏰ 排程器已啟動 - 每 {interval_minutes} 分鐘執行一次檢測")


def stop_scheduler():
    """停止排程器"""
    if scheduler.running:
        scheduler.shutdown()
        print("⏰ 排程器已停止")


async def run_once():
    """執行一次檢測（手動觸發）"""
    await scheduled_check()
