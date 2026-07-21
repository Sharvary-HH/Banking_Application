import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


class AccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, account: Account) -> Account:
        self.db.add(account)
        await self.db.flush()
        return account

    async def get_by_id(self, account_id: uuid.UUID) -> Account | None:
        return await self.db.get(Account, account_id)

    async def get_owned_by_user(self, account_id: uuid.UUID, user_id: uuid.UUID) -> Account | None:
        """Ownership-scoped lookup — the only way account-facing code should ever
        fetch an account, so a customer can never act on/see another user's account by ID."""
        result = await self.db.execute(
            select(Account).where(Account.id == account_id, Account.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_locked(self, account_id: uuid.UUID) -> Account | None:
        """Row-level lock (SELECT ... FOR UPDATE) used inside a transfer/deposit/withdraw
        DB transaction so concurrent mutations on the same account serialize correctly."""
        result = await self.db.execute(
            select(Account).where(Account.id == account_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_owned_locked(self, account_id: uuid.UUID, user_id: uuid.UUID) -> Account | None:
        """Ownership check and row lock in one query, for deposit/withdraw where both
        accounts involved always belong to the caller."""
        result = await self.db.execute(
            select(Account)
            .where(Account.id == account_id, Account.user_id == user_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[Account]:
        result = await self.db.execute(
            select(Account).where(Account.user_id == user_id).order_by(Account.created_at)
        )
        return list(result.scalars().all())

    async def account_number_exists(self, account_number: str) -> bool:
        result = await self.db.execute(select(Account.id).where(Account.account_number == account_number))
        return result.scalar_one_or_none() is not None

    async def get_by_account_number(self, account_number: str) -> Account | None:
        result = await self.db.execute(select(Account).where(Account.account_number == account_number))
        return result.scalar_one_or_none()
