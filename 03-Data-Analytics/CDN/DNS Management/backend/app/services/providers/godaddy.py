from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.services.providers.base import ProviderClient, ProviderDomain


class GoDaddyClient(ProviderClient):
    BASE_URLS = {
        "production": "https://api.godaddy.com",
        "ote": "https://api.ote-godaddy.com",
    }

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        environment: str = "production",
        *,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.environment = environment if environment in self.BASE_URLS else "production"
        self._client = http_client

    @property
    def base_url(self) -> str:
        return self.BASE_URLS[self.environment]

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"sso-key {self.api_key}:{self.api_secret}",
            "Accept": "application/json",
        }

    async def list_domains(self) -> list[ProviderDomain]:
        client = self._client or httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        close_client = self._client is None
        try:
            response = await client.get("/v1/domains", headers=self._headers())
            response.raise_for_status()
            payload: list[dict[str, Any]] = response.json()
            domains: list[ProviderDomain] = []
            for item in payload:
                nameservers = item.get("nameServers")
                domains.append(
                    ProviderDomain(
                        name=item.get("domain", ""),
                        status=item.get("status"),
                        expires_at=_parse_datetime(item.get("expires")),
                        auto_renew=item.get("renewAuto", False),
                        nameservers=nameservers if isinstance(nameservers, list) else None,
                    )
                )
            return domains
        finally:
            if close_client:
                await client.aclose()

    async def validate_credentials(self) -> bool:
        client = self._client or httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        close_client = self._client is None
        try:
            response = await client.get("/v1/domains?limit=1", headers=self._headers())
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError:
            return False
        finally:
            if close_client:
                await client.aclose()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

