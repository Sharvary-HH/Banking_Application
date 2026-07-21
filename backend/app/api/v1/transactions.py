import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction import (
    DepositRequest,
    PaginatedTransactions,
    TransactionOut,
    TransferRequest,
    TransferResponse,
    WithdrawRequest,
)
from app.services.transaction_service import TransactionService

router = APIRouter(tags=["transactions"])


@router.post("/accounts/{account_id}/deposit", response_model=TransactionOut)
async def deposit(
    account_id: uuid.UUID,
    payload: DepositRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TransactionService(db)
    return await service.deposit(current_user.id, account_id, payload.amount_cents, payload.description)


@router.post("/accounts/{account_id}/withdraw", response_model=TransactionOut)
async def withdraw(
    account_id: uuid.UUID,
    payload: WithdrawRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TransactionService(db)
    return await service.withdraw(current_user.id, account_id, payload.amount_cents, payload.description)


@router.post("/transfers", response_model=TransferResponse)
async def transfer(
    payload: TransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TransactionService(db)
    return await service.transfer(
        current_user.id,
        payload.from_account_id,
        payload.to_account_id,
        payload.amount_cents,
        payload.description,
    )


@router.get("/accounts/{account_id}/transactions", response_model=PaginatedTransactions)
async def list_transactions(
    account_id: uuid.UUID,
    type: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    min_amount_cents: int | None = Query(default=None),
    max_amount_cents: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TransactionService(db)
    return await service.list_transactions(
        current_user.id,
        account_id,
        type_filter=type,
        start_date=start_date,
        end_date=end_date,
        min_amount_cents=min_amount_cents,
        max_amount_cents=max_amount_cents,
        page=page,
        page_size=page_size,
    )
