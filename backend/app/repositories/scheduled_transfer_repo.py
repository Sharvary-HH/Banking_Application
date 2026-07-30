import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_transfer import ScheduledTransfer


class ScheduledTransferRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, scheduled_transfer: ScheduledTransfer) -> ScheduledTransfer:
        self.db.add(scheduled_transfer)
        await self.db.flush()
        return scheduled_transfer

    async def list_for_user(self, user_id: uuid.UUID) -> list[ScheduledTransfer]:
        result = await self.db.execute(
            select(ScheduledTransfer)
            .where(ScheduledTransfer.user_id == user_id)
            .order_by(ScheduledTransfer.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_owned_by_user(self, scheduled_transfer_id: uuid.UUID, user_id: uuid.UUID) -> ScheduledTransfer | None:
        result = await self.db.execute(
            select(ScheduledTransfer).where(
                ScheduledTransfer.id == scheduled_transfer_id, ScheduledTransfer.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_due(self, as_of: datetime) -> list[ScheduledTransfer]:
        result = await self.db.execute(
            select(ScheduledTransfer).where(
                ScheduledTransfer.is_active.is_(True), ScheduledTransfer.next_run_at <= as_of
            )
        )
        return list(result.scalars().all())
