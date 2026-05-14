from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(slots=True)
class ProviderDomain:
    name: str
    status: str | None = None
    expires_at: datetime | None = None
    auto_renew: bool = False
    nameservers: list[str] | None = None


class ProviderClient(Protocol):
    async def list_domains(self) -> list[ProviderDomain]:
        ...

    async def validate_credentials(self) -> bool:
        ...

