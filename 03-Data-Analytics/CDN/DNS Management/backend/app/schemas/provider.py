from pydantic import BaseModel

from app.models.provider import ProviderSlug, ProviderType


class ProviderRead(BaseModel):
    id: int
    name: str
    slug: ProviderSlug
    provider_type: ProviderType

    class Config:
        from_attributes = True

