from datetime import datetime

from pydantic import BaseModel, Field


class DomainRead(BaseModel):
    id: int
    account_id: int
    name: str
    status: str | None = None
    expires_at: datetime | None = None
    nameservers: list[str] | None = None
    auto_renew: bool = False
    last_synced_at: datetime | None = None

    class Config:
        from_attributes = True


class DomainListResponse(BaseModel):
    total: int
    items: list[DomainRead]


class DomainSyncRequest(BaseModel):
    account_id: int = Field(..., ge=1)

