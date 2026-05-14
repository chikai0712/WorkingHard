from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.sync_job import SyncJob
from app.schemas.sync_job import SyncJobListResponse, SyncJobRead

router = APIRouter()


@router.get("/", response_model=SyncJobListResponse)
def list_sync_jobs(db: Session = Depends(get_db)) -> SyncJobListResponse:
    stmt = select(SyncJob).order_by(SyncJob.id.desc()).limit(50)
    jobs = db.execute(stmt).scalars().all()
    return SyncJobListResponse(items=[SyncJobRead.model_validate(job) for job in jobs])

