from datetime import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.account import Account


class ProviderType(str, enum.Enum):
    registrar = "registrar"
    dns = "dns"
    cdn = "cdn"


class ProviderSlug(str, enum.Enum):
    godaddy = "godaddy"
    namecheap = "namecheap"


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(Enum(ProviderSlug), nullable=False, unique=True)
    provider_type: Mapped[str] = mapped_column(Enum(ProviderType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    accounts: Mapped[list["Account"]] = relationship(back_populates="provider")
