from __future__ import annotations

from datetime import datetime
import xml.etree.ElementTree as ET

import httpx

from app.services.providers.base import ProviderClient, ProviderDomain


class NamecheapClient(ProviderClient):
    BASE_URLS = {
        "sandbox": "https://api.sandbox.namecheap.com/xml.response",
        "production": "https://api.namecheap.com/xml.response",
    }

    def __init__(
        self,
        api_user: str,
        api_key: str,
        client_ip: str,
        username: str | None = None,
        environment: str = "sandbox",
        *,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.api_user = api_user
        self.api_key = api_key
        self.client_ip = client_ip
        self.username = username or api_user
        self.environment = environment if environment in self.BASE_URLS else "sandbox"
        self._client = http_client

    @property
    def base_url(self) -> str:
        return self.BASE_URLS[self.environment]

    def _common_params(self) -> dict[str, str]:
        return {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.username,
            "ClientIp": self.client_ip,
        }

    async def list_domains(self) -> list[ProviderDomain]:
        params = {
            **self._common_params(),
            "Command": "namecheap.domains.getList",
            "ListType": "ALL",
            "PageSize": "100",
        }
        return await self._request_domains(params)

    async def validate_credentials(self) -> bool:
        params = {
            **self._common_params(),
            "Command": "namecheap.domains.getList",
            "PageSize": "1",
        }
        try:
            await self._request_domains(params)
            return True
        except httpx.HTTPError:
            return False

    async def _request_domains(self, params: dict[str, str]) -> list[ProviderDomain]:
        client = self._client or httpx.AsyncClient(timeout=30.0)
        close_client = self._client is None
        try:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return _parse_domain_list(response.text)
        finally:
            if close_client:
                await client.aclose()


def _parse_domain_list(xml_body: str) -> list[ProviderDomain]:
    root = ET.fromstring(xml_body)
    domains: list[ProviderDomain] = []
    for domain_elem in root.findall(".//Domain"):
        name = domain_elem.attrib.get("Name", "")
        expires = domain_elem.attrib.get("Expires")
        auto_renew = domain_elem.attrib.get("AutoRenew") == "true"
        status = domain_elem.attrib.get("Status")
        domains.append(
            ProviderDomain(
                name=name,
                status=status,
                expires_at=_parse_date(expires),
                auto_renew=auto_renew,
                nameservers=None,
            )
        )
    return domains


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%m/%d/%Y")
    except ValueError:
        return None

