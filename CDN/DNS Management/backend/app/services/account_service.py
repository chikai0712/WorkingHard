from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import encrypt_value, decrypt_value
from app.models.account import Account
from app.models.provider import Provider, ProviderSlug, ProviderType
from app.schemas.account import AccountCreate, AccountUpdate
from app.services.providers.registry import build_provider_client


class AccountService:
    def __init__(self, db: Session):
        self.db = db

    def list_accounts(self) -> Sequence[Account]:
        stmt = select(Account).options(joinedload(Account.provider)).order_by(Account.id.desc())
        return self.db.execute(stmt).scalars().all()

    def get_account(self, account_id: int) -> Account | None:
        stmt = (
            select(Account)
            .where(Account.id == account_id)
            .options(joinedload(Account.provider))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_account(self, payload: AccountCreate) -> Account:
        provider = self._ensure_provider(payload.provider_slug)
        account = Account(
            provider_id=provider.id,
            label=payload.label,
            api_key=encrypt_value(payload.api_key),
            api_secret=encrypt_value(payload.api_secret),
            extra_config=payload.extra_config or {},
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def update_account(self, account_id: int, payload: AccountUpdate) -> Account | None:
        account = self.get_account(account_id)
        if not account:
            return None

        if payload.label is not None:
            account.label = payload.label
        if payload.api_key is not None:
            account.api_key = encrypt_value(payload.api_key)
        if payload.api_secret is not None:
            account.api_secret = encrypt_value(payload.api_secret)
        if payload.extra_config is not None:
            account.extra_config = payload.extra_config

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    async def test_connection(self, account_id: int) -> bool:
        account = self.get_account(account_id)
        if not account:
            raise ValueError("Account not found")
        client = build_provider_client(account)
        return await client.validate_credentials()

    def _ensure_provider(self, slug: ProviderSlug) -> Provider:
        provider = self.db.execute(
            select(Provider).where(Provider.slug == slug)
        ).scalar_one_or_none()
        if provider:
            return provider

        provider = Provider(
            name=slug.value.title(),
            slug=slug,
            provider_type=ProviderType.registrar,
        )
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def reveal_secret(self, encrypted_value: str | None) -> str | None:
        return decrypt_value(encrypted_value)

