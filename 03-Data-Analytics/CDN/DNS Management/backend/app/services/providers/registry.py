from __future__ import annotations

from typing import Optional

from app.core.security import decrypt_value
from app.models.account import Account
from app.models.provider import ProviderSlug
from app.services.providers.base import ProviderClient
from app.services.providers.godaddy import GoDaddyClient
from app.services.providers.namecheap import NamecheapClient


class ProviderRegistryError(RuntimeError):
    pass


def build_provider_client(account: Account) -> ProviderClient:
    provider = account.provider
    if provider is None:
        raise ProviderRegistryError("Account provider is not loaded.")

    try:
        slug = ProviderSlug(provider.slug)
    except ValueError as exc:  # pragma: no cover - validated in tests
        raise ProviderRegistryError(f"Provider slug {provider.slug} is not supported.") from exc
    if slug == ProviderSlug.godaddy:
        api_key = _require_secret(decrypt_value(account.api_key), "GoDaddy api_key")
        api_secret = _require_secret(decrypt_value(account.api_secret), "GoDaddy api_secret")
        environment = account.extra_config.get("environment") if account.extra_config else "production"
        return GoDaddyClient(api_key=api_key, api_secret=api_secret, environment=environment)

    if slug == ProviderSlug.namecheap:
        api_key = _require_secret(decrypt_value(account.api_key), "Namecheap api_key")
        extra = account.extra_config or {}
        api_user = extra.get("api_user") or _require_secret(extra.get("ApiUser"), "Namecheap api_user")
        client_ip = extra.get("client_ip") or _require_secret(extra.get("ClientIp"), "Namecheap client_ip")
        username = extra.get("username")
        environment = extra.get("environment", "sandbox")
        return NamecheapClient(
            api_user=api_user,
            api_key=api_key,
            client_ip=client_ip,
            username=username,
            environment=environment,
        )

    raise ProviderRegistryError(f"Provider slug {slug} is not supported.")


def _require_secret(value: Optional[str], field_name: str) -> str:
    if not value:
        raise ProviderRegistryError(f"{field_name} is required but missing.")
    return value

