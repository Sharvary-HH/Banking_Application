from datetime import datetime

from pydantic import BaseModel


class TypeBreakdown(BaseModel):
    type: str
    total_cents: int
    count: int


class MonthlyBreakdown(BaseModel):
    month: str  # "YYYY-MM"
    credits_cents: int
    debits_cents: int
    net_cents: int


class AnalyticsSummary(BaseModel):
    start_date: datetime | None
    end_date: datetime | None
    total_credits_cents: int
    total_debits_cents: int
    net_cents: int
    by_type: list[TypeBreakdown]
    by_month: list[MonthlyBreakdown]
