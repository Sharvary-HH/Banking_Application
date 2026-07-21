import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepositRequest(BaseModel):
    amount_cents: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=255)


class WithdrawRequest(BaseModel):
    amount_cents: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=255)


class TransferRequest(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount_cents: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=255)


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    related_account_id: uuid.UUID | None
    type: str
    amount_cents: int
    balance_after_cents: int
    reference_id: uuid.UUID
    description: str | None
    created_at: datetime


class TransferResponse(BaseModel):
    debit: TransactionOut
    credit: TransactionOut


class PaginatedTransactions(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int
