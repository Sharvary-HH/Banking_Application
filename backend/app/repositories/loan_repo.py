import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan import Loan


class LoanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, loan: Loan) -> Loan:
        self.db.add(loan)
        await self.db.flush()
        return loan

    async def get_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        return await self.db.get(Loan, loan_id)

    async def get_owned_by_user(self, loan_id: uuid.UUID, user_id: uuid.UUID) -> Loan | None:
        result = await self.db.execute(select(Loan).where(Loan.id == loan_id, Loan.user_id == user_id))
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[Loan]:
        result = await self.db.execute(select(Loan).where(Loan.user_id == user_id).order_by(Loan.created_at.desc()))
        return list(result.scalars().all())

    async def list_all(self, status_filter: str | None = None) -> list[Loan]:
        stmt = select(Loan).order_by(Loan.created_at.desc())
        if status_filter:
            stmt = stmt.where(Loan.status == status_filter)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
