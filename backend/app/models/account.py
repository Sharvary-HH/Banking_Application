import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class AccountType(str, Enum):
    SAVINGS = "savings"
    CHECKING = "checking"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    account_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Money is always stored as an integer count of cents. Never use float for currency.
    balance_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # Optimistic-locking guard, incremented on every balance mutation alongside the
    # SELECT ... FOR UPDATE row lock taken in the transaction service.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
