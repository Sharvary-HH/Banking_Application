import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_transfer import ScheduledTransfer
from app.repositories.account_repo import AccountRepository
from app.repositories.scheduled_transfer_repo import ScheduledTransferRepository


class ScheduledTransferService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.scheduled_transfers = ScheduledTransferRepository(db)
        self.accounts = AccountRepository(db)

    async def create(
        self,
        user_id: uuid.UUID,
        from_account_id: uuid.UUID,
        to_account_id: uuid.UUID,
        amount_cents: int,
        description: str | None,
        frequency: str,
        start_at: datetime | None,
        end_date: datetime | None,
    ) -> ScheduledTransfer:
        if from_account_id == to_account_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot schedule a transfer to the same account")

        from_account = await self.accounts.get_owned_by_user(from_account_id, user_id)
        if from_account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        to_account = await self.accounts.get_by_id(to_account_id)
        if to_account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination account not found")

        next_run_at = start_at or datetime.now(timezone.utc)

        scheduled_transfer = await self.scheduled_transfers.create(
            ScheduledTransfer(
                user_id=user_id,
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                amount_cents=amount_cents,
                description=description,
                frequency=frequency,
                next_run_at=next_run_at,
                end_date=end_date,
            )
        )
        await self.db.commit()
        return scheduled_transfer

    async def list_for_user(self, user_id: uuid.UUID) -> list[ScheduledTransfer]:
        return await self.scheduled_transfers.list_for_user(user_id)

    async def cancel(self, scheduled_transfer_id: uuid.UUID, user_id: uuid.UUID) -> ScheduledTransfer:
        scheduled_transfer = await self.scheduled_transfers.get_owned_by_user(scheduled_transfer_id, user_id)
        if scheduled_transfer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled transfer not found")
        scheduled_transfer.is_active = False
        await self.db.commit()
        return scheduled_transfer
