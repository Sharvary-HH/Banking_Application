import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.account import AccountType


class AccountCreate(BaseModel):
    account_type: AccountType


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_number: str
    account_type: str
    balance_cents: int
    created_at: datetime

    @field_validator("account_type", mode="before")
    @classmethod
    def _coerce_enum(cls, v: object) -> str:
        return v.value if isinstance(v, AccountType) else v
