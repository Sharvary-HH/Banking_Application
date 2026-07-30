import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.loan import EmiCalculationRequest, EmiCalculationResponse, LoanApplyRequest, LoanOut
from app.services.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("/calculate-emi", response_model=EmiCalculationResponse)
async def calculate_emi_endpoint(
    payload: EmiCalculationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # noqa: ARG001 — auth required, no persistence
):
    return LoanService(db).calculate_emi(payload.principal_cents, payload.annual_interest_rate_bps, payload.term_months)


@router.post("", response_model=LoanOut)
async def apply_for_loan(
    payload: LoanApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LoanService(db)
    return await service.apply(
        current_user.id,
        payload.disbursement_account_id,
        payload.principal_cents,
        payload.annual_interest_rate_bps,
        payload.term_months,
    )


@router.get("", response_model=list[LoanOut])
async def list_my_loans(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = LoanService(db)
    return await service.list_for_user(current_user.id)


@router.get("/{loan_id}", response_model=LoanOut)
async def get_my_loan(
    loan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LoanService(db)
    return await service.get_owned_or_404(loan_id, current_user.id)
