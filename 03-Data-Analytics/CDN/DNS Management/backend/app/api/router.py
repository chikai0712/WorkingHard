from fastapi import APIRouter

from app.api.routes import accounts, domains, health, metrics, sync_jobs

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(metrics.router, tags=["metrics"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(domains.router, prefix="/domains", tags=["domains"])
api_router.include_router(sync_jobs.router, prefix="/sync-jobs", tags=["sync"])
