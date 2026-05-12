from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.workers.sync_runner import init_scheduler, shutdown_scheduler

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
async def on_startup() -> None:
    init_scheduler()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    shutdown_scheduler()


@app.get("/healthz", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_v1_prefix)
