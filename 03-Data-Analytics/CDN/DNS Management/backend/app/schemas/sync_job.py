from datetime import datetime

from pydantic import BaseModel

from app.models.sync_job import SyncStatus


class SyncJobRead(BaseModel):
    id: int
    account_id: int
    provider_slug: str
    status: SyncStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str | None = None

    class Config:
        from_attributes = True


class SyncJobListResponse(BaseModel):
    items: list[SyncJobRead]

