import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.beneficiary import Beneficiary
from app.repositories.account_repo import AccountRepository
from app.repositories.beneficiary_repo import BeneficiaryRepository
from app.schemas.beneficiary import BeneficiaryOut


class BeneficiaryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.beneficiaries = BeneficiaryRepository(db)
        self.accounts = AccountRepository(db)

    async def create(self, owner_user_id: uuid.UUID, nickname: str, account_id: uuid.UUID) -> BeneficiaryOut:
        account = await self.accounts.get_by_id(account_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        beneficiary = await self.beneficiaries.create(
            Beneficiary(owner_user_id=owner_user_id, nickname=nickname, account_id=account_id)
        )
        await self.db.commit()
        return self._to_out(beneficiary, account.account_number)

    async def list_for_user(self, owner_user_id: uuid.UUID) -> list[BeneficiaryOut]:
        beneficiaries = await self.beneficiaries.list_for_user(owner_user_id)
        out = []
        for b in beneficiaries:
            account = await self.accounts.get_by_id(b.account_id)
            out.append(self._to_out(b, account.account_number if account else "unknown"))
        return out

    @staticmethod
    def _to_out(beneficiary: Beneficiary, account_number: str) -> BeneficiaryOut:
        return BeneficiaryOut(
            id=beneficiary.id,
            nickname=beneficiary.nickname,
            account_id=beneficiary.account_id,
            account_number=account_number,
            created_at=beneficiary.created_at,
        )

    async def delete(self, beneficiary_id: uuid.UUID, owner_user_id: uuid.UUID) -> None:
        beneficiary = await self.beneficiaries.get_owned_by_user(beneficiary_id, owner_user_id)
        if beneficiary is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Beneficiary not found")
        await self.beneficiaries.delete(beneficiary)
        await self.db.commit()
