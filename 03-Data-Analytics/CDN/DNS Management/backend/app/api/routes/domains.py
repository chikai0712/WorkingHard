from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import Domain
from app.schemas.domain import DomainListResponse, DomainRead, DomainSyncRequest
from app.services.domain_service import DomainService

router = APIRouter()


@router.get("/", response_model=DomainListResponse)
def list_domains(
    account_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
) -> DomainListResponse:
    service = DomainService(db)
    offset = (page - 1) * page_size
    total, items = service.list_domains(account_id=account_id, search=search, limit=page_size, offset=offset)
    return DomainListResponse(total=total, items=[DomainRead.model_validate(item) for item in items])


@router.get("/{domain_id}", response_model=DomainRead)
def get_domain(domain_id: int, db: Session = Depends(get_db)) -> DomainRead:
    domain = db.get(Domain, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return DomainRead.model_validate(domain)


@router.post("/sync", response_model=dict)
async def sync_domains(payload: DomainSyncRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    service = DomainService(db)
    job = await service.sync_account(payload)
    return {"status": job.status, "message": job.message or ""}

