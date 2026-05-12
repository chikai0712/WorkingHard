from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _run_sync_job():
    db = SessionLocal()
    try:
        service = SyncService(db)
        count = await service.sync_all_accounts()
        logger.info("Domain sync completed", extra={"accounts": count})
    except Exception as exc:  # pragma: no cover
        logger.exception("Domain sync failed: %s", exc)
    finally:
        db.close()


def init_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
    scheduler.add_job(
        _run_sync_job,
        "interval",
        minutes=30,
        id="domain_sync",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None

