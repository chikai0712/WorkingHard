from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.schemas.domain import DomainSyncRequest
from app.services.domain_service import DomainService


class SyncService:
    def __init__(self, db: Session):
        self.db = db
        self.domain_service = DomainService(db)

    async def sync_all_accounts(self) -> int:
        accounts = self.db.execute(select(Account.id)).scalars().all()
        count = 0
        for account_id in accounts:
            await self.domain_service.sync_account(DomainSyncRequest(account_id=account_id))
            count += 1
        return count

