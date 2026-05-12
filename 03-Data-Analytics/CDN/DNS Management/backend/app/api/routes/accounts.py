from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate, AccountWithProvider
from app.services.account_service import AccountService

router = APIRouter()


@router.get("/", response_model=list[AccountWithProvider])
def list_accounts(db: Session = Depends(get_db)) -> list[AccountWithProvider]:
    service = AccountService(db)
    accounts = service.list_accounts()
    return [
        AccountWithProvider(
            id=account.id,
            provider_slug=account.provider.slug,
            provider_name=account.provider.name,
            label=account.label,
            created_at=account.created_at,
        )
        for account in accounts
    ]


@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)) -> AccountRead:
    service = AccountService(db)
    account = service.create_account(payload)
    return AccountRead(
        id=account.id,
        provider_slug=account.provider.slug,
        label=account.label,
        created_at=account.created_at,
    )


@router.get("/{account_id}", response_model=AccountRead)
def get_account(account_id: int, db: Session = Depends(get_db)) -> AccountRead:
    service = AccountService(db)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountRead(
        id=account.id,
        provider_slug=account.provider.slug,
        label=account.label,
        created_at=account.created_at,
    )


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
) -> AccountRead:
    service = AccountService(db)
    account = service.update_account(account_id, payload)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountRead(
        id=account.id,
        provider_slug=account.provider.slug,
        label=account.label,
        created_at=account.created_at,
    )


@router.post("/{account_id}/test", status_code=status.HTTP_200_OK)
async def test_account(account_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    service = AccountService(db)
    try:
        ok = await service.test_connection(account_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Account not found") from None
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"success": ok}

