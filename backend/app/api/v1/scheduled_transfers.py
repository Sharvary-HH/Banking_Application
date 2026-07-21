import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.scheduled_transfer import ScheduledTransferCreate, ScheduledTransferOut
from app.services.scheduled_transfer_service import ScheduledTransferService

router = APIRouter(prefix="/scheduled-transfers", tags=["scheduled-transfers"])


@router.post("", response_model=ScheduledTransferOut)
async def create_scheduled_transfer(
    payload: ScheduledTransferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ScheduledTransferService(db)
    return await service.create(
        current_user.id,
        payload.from_account_id,
        payload.to_account_id,
        payload.amount_cents,
        payload.description,
        payload.frequency.value,
        payload.start_at,
        payload.end_date,
    )


@router.get("", response_model=list[ScheduledTransferOut])
async def list_scheduled_transfers(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = ScheduledTransferService(db)
    return await service.list_for_user(current_user.id)


@router.post("/{scheduled_transfer_id}/cancel", response_model=ScheduledTransferOut)
async def cancel_scheduled_transfer(
    scheduled_transfer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ScheduledTransferService(db)
    return await service.cancel(scheduled_transfer_id, current_user.id)
