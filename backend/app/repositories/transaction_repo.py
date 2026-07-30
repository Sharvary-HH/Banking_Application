import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        await self.db.flush()
        return transaction

    async def list_for_account(
        self,
        account_id: uuid.UUID,
        *,
        type_filter: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        min_amount_cents: int | None = None,
        max_amount_cents: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Transaction], int]:
        stmt = select(Transaction).where(Transaction.account_id == account_id)

        if type_filter:
            stmt = stmt.where(Transaction.type == type_filter)
        if start_date:
            stmt = stmt.where(Transaction.created_at >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.created_at <= end_date)
        if min_amount_cents is not None:
            stmt = stmt.where(Transaction.amount_cents >= min_amount_cents)
        if max_amount_cents is not None:
            stmt = stmt.where(Transaction.amount_cents <= max_amount_cents)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Transaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def list_for_analytics(
        self,
        user_id: uuid.UUID,
        *,
        account_id: uuid.UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Transaction]:
        """All transactions across every account the user owns (or just one, if
        account_id is given) — joined through Account so this can never see another
        user's transactions, same ownership discipline as everywhere else."""
        stmt = select(Transaction).join(Account, Transaction.account_id == Account.id).where(Account.user_id == user_id)

        if account_id is not None:
            stmt = stmt.where(Transaction.account_id == account_id)
        if start_date:
            stmt = stmt.where(Transaction.created_at >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.created_at <= end_date)

        result = await self.db.execute(stmt.order_by(Transaction.created_at))
        return list(result.scalars().all())
