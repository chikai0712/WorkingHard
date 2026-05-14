from types import SimpleNamespace

import pytest

from app.services.providers.registry import ProviderRegistryError, build_provider_client


def test_missing_provider_raises():
    account = SimpleNamespace(provider=None, api_key="", api_secret="", extra_config={}, label="demo")
    with pytest.raises(ProviderRegistryError):
        build_provider_client(account)  # type: ignore[arg-type]


def test_unsupported_provider():
    provider = SimpleNamespace(slug="unsupported", name="Unsupported")
    account = SimpleNamespace(provider=provider, api_key="", api_secret="", extra_config={}, label="demo")
    with pytest.raises(ProviderRegistryError):
        build_provider_client(account)  # type: ignore[arg-type]

