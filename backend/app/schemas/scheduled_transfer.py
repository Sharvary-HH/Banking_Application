import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.scheduled_transfer import TransferFrequency


class ScheduledTransferCreate(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount_cents: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=255)
    frequency: TransferFrequency
    start_at: datetime | None = None
    end_date: datetime | None = None


class ScheduledTransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount_cents: int
    description: str | None
    frequency: str
    next_run_at: datetime
    end_date: datetime | None
    is_active: bool
    last_run_at: datetime | None
    last_run_status: str | None
    created_at: datetime
