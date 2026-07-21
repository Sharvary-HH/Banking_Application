import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EmiCalculationRequest(BaseModel):
    principal_cents: int = Field(gt=0)
    annual_interest_rate_bps: int = Field(ge=0, le=10_000)  # 0%–100% APR
    term_months: int = Field(gt=0, le=480)  # up to 40 years


class EmiCalculationResponse(BaseModel):
    emi_cents: int
    total_payment_cents: int
    total_interest_cents: int


class LoanApplyRequest(EmiCalculationRequest):
    disbursement_account_id: uuid.UUID


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    disbursement_account_id: uuid.UUID
    principal_cents: int
    annual_interest_rate_bps: int
    term_months: int
    emi_cents: int
    status: str
    decided_at: datetime | None
    created_at: datetime


class AdminLoanOut(LoanOut):
    user_id: uuid.UUID
    applicant_email: str
