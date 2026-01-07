from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.provider import ProviderSlug


class AccountBase(BaseModel):
    provider_slug: ProviderSlug
    label: str = Field(..., max_length=100)
    api_key: str = Field(..., min_length=1)
    api_secret: Optional[str] = None
    extra_config: dict | None = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    label: str | None = Field(default=None, max_length=100)
    api_key: str | None = None
    api_secret: str | None = None
    extra_config: dict | None = None


class AccountRead(BaseModel):
    id: int
    provider_slug: ProviderSlug
    label: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AccountWithProvider(AccountRead):
    provider_name: str

