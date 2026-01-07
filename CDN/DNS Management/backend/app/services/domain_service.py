from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.account import Account
from app.models.domain import Domain
from app.models.sync_job import SyncJob, SyncStatus
from app.schemas.domain import DomainSyncRequest
from app.services.providers.registry import build_provider_client


class DomainService:
    def __init__(self, db: Session):
        self.db = db

    def list_domains(
        self,
        *,
        account_id: int | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[Domain]]:
        stmt: Select[tuple[Domain]] = select(Domain).options(joinedload(Domain.account))
        count_stmt = select(func.count()).select_from(Domain)

        if account_id:
            stmt = stmt.where(Domain.account_id == account_id)
            count_stmt = count_stmt.where(Domain.account_id == account_id)
        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(Domain.name.ilike(like_pattern))
            count_stmt = count_stmt.where(Domain.name.ilike(like_pattern))

        stmt = stmt.order_by(Domain.name).offset(offset).limit(limit)

        domains = self.db.execute(stmt).scalars().all()
        total = self.db.execute(count_stmt).scalar_one()
        return total, domains

    async def sync_account(self, request: DomainSyncRequest) -> SyncJob:
        account = self.db.execute(
            select(Account)
            .where(Account.id == request.account_id)
            .options(joinedload(Account.provider))
        ).scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")

        job = SyncJob(
            account_id=account.id,
            provider_slug=account.provider.slug,
            status=SyncStatus.running,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        try:
            client = build_provider_client(account)
            provider_domains = await client.list_domains()
            self._sync_domains(account.id, provider_domains)
            job.status = SyncStatus.success
            job.message = f"Synced {len(provider_domains)} domains"
        except Exception as exc:  # pragma: no cover
            job.status = SyncStatus.failed
            job.message = str(exc)
        finally:
            job.finished_at = datetime.now(timezone.utc)
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)

        return job

    def _sync_domains(self, account_id: int, provider_domains: Sequence) -> None:
        existing_domains = {
            domain.name: domain
            for domain in self.db.execute(
                select(Domain).where(Domain.account_id == account_id)
            ).scalars()
        }
        now = datetime.now(timezone.utc)
        for payload in provider_domains:
            domain = existing_domains.get(payload.name)
            if not domain:
                domain = Domain(account_id=account_id, name=payload.name)
            domain.status = payload.status
            domain.expires_at = payload.expires_at
            domain.auto_renew = payload.auto_renew
            domain.nameservers = payload.nameservers
            domain.last_synced_at = now
            self.db.add(domain)

        self.db.commit()

