import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.beneficiary import BeneficiaryCreate, BeneficiaryOut
from app.services.beneficiary_service import BeneficiaryService

router = APIRouter(prefix="/beneficiaries", tags=["beneficiaries"])


@router.post("", response_model=BeneficiaryOut, status_code=status.HTTP_201_CREATED)
async def create_beneficiary(
    payload: BeneficiaryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BeneficiaryService(db)
    return await service.create(current_user.id, payload.nickname, payload.account_id)


@router.get("", response_model=list[BeneficiaryOut])
async def list_beneficiaries(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = BeneficiaryService(db)
    return await service.list_for_user(current_user.id)


@router.delete("/{beneficiary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_beneficiary(
    beneficiary_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BeneficiaryService(db)
    await service.delete(beneficiary_id, current_user.id)
