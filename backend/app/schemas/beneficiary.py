import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BeneficiaryCreate(BaseModel):
    nickname: str = Field(min_length=1, max_length=100)
    account_id: uuid.UUID


class BeneficiaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nickname: str
    account_id: uuid.UUID
    account_number: str
    created_at: datetime


class AccountLookupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_number: str
    account_type: str
