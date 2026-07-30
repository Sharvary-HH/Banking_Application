import secrets
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.repositories.account_repo import AccountRepository


class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.accounts = AccountRepository(db)

    async def create_account(self, user_id: uuid.UUID, account_type: str) -> Account:
        account_number = await self._generate_unique_account_number()
        account = Account(user_id=user_id, account_number=account_number, account_type=account_type, balance_cents=0)
        await self.accounts.create(account)
        await self.db.commit()
        return account

    async def list_accounts(self, user_id: uuid.UUID) -> list[Account]:
        return await self.accounts.list_for_user(user_id)

    async def get_account_or_404(self, account_id: uuid.UUID, user_id: uuid.UUID) -> Account:
        # Ownership-scoped lookup: an account that exists but belongs to someone else
        # returns the same 404 as one that doesn't exist at all — no IDOR signal leak.
        account = await self.accounts.get_owned_by_user(account_id, user_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return account

    async def lookup_by_account_number(self, account_number: str) -> Account:
        # Deliberately NOT ownership-scoped — this backs the "add a beneficiary by account
        # number" flow, so any authenticated user can resolve any account number. The
        # response schema (AccountLookupOut) only ever exposes id/number/type, never
        # balance or the owning user, so this can't be used to snoop on someone's finances.
        account = await self.accounts.get_by_account_number(account_number)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return account

    async def _generate_unique_account_number(self) -> str:
        for _ in range(10):
            candidate = "".join(secrets.choice("0123456789") for _ in range(10))
            if not await self.accounts.account_number_exists(candidate):
                return candidate
        raise RuntimeError("Failed to generate a unique account number")
