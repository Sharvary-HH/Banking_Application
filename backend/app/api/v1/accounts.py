import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.account import AccountCreate, AccountOut
from app.schemas.beneficiary import AccountLookupOut
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AccountService(db)
    return await service.create_account(current_user.id, payload.account_type.value)


@router.get("", response_model=list[AccountOut])
async def list_accounts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = AccountService(db)
    return await service.list_accounts(current_user.id)


@router.get("/lookup", response_model=AccountLookupOut)
async def lookup_account(
    account_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # noqa: ARG001 — auth required, result unused by design
):
    """Resolves an account number to its id/type only (never balance or owner) — this is
    what lets a user save a beneficiary by account number without seeing whose it is.
    Registered before /{account_id} so "lookup" isn't swallowed as a UUID path param."""
    service = AccountService(db)
    return await service.lookup_by_account_number(account_number)


@router.get("/{account_id}", response_model=AccountOut)
async def get_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AccountService(db)
    return await service.get_account_or_404(account_id, current_user.id)
