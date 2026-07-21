import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.beneficiary import Beneficiary


class BeneficiaryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, beneficiary: Beneficiary) -> Beneficiary:
        self.db.add(beneficiary)
        await self.db.flush()
        return beneficiary

    async def list_for_user(self, owner_user_id: uuid.UUID) -> list[Beneficiary]:
        result = await self.db.execute(
            select(Beneficiary).where(Beneficiary.owner_user_id == owner_user_id).order_by(Beneficiary.created_at)
        )
        return list(result.scalars().all())

    async def get_owned_by_user(self, beneficiary_id: uuid.UUID, owner_user_id: uuid.UUID) -> Beneficiary | None:
        result = await self.db.execute(
            select(Beneficiary).where(Beneficiary.id == beneficiary_id, Beneficiary.owner_user_id == owner_user_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, beneficiary: Beneficiary) -> None:
        await self.db.delete(beneficiary)
        await self.db.flush()
