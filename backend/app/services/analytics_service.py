import uuid
from collections import defaultdict
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import TransactionType
from app.repositories.account_repo import AccountRepository
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.analytics import AnalyticsSummary, MonthlyBreakdown, TypeBreakdown

CREDIT_TYPES = {TransactionType.DEPOSIT.value, TransactionType.TRANSFER_IN.value, TransactionType.LOAN_DISBURSEMENT.value}
DEBIT_TYPES = {TransactionType.WITHDRAW.value, TransactionType.TRANSFER_OUT.value}


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.accounts = AccountRepository(db)
        self.transactions = TransactionRepository(db)

    async def get_summary(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID | None,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> AnalyticsSummary:
        if account_id is not None:
            account = await self.accounts.get_owned_by_user(account_id, user_id)
            if account is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        transactions = await self.transactions.list_for_analytics(
            user_id, account_id=account_id, start_date=start_date, end_date=end_date
        )

        type_totals: dict[str, int] = defaultdict(int)
        type_counts: dict[str, int] = defaultdict(int)
        month_credits: dict[str, int] = defaultdict(int)
        month_debits: dict[str, int] = defaultdict(int)
        total_credits = 0
        total_debits = 0

        for tx in transactions:
            type_totals[tx.type] += tx.amount_cents
            type_counts[tx.type] += 1
            month_key = tx.created_at.strftime("%Y-%m")

            if tx.type in CREDIT_TYPES:
                total_credits += tx.amount_cents
                month_credits[month_key] += tx.amount_cents
            elif tx.type in DEBIT_TYPES:
                total_debits += tx.amount_cents
                month_debits[month_key] += tx.amount_cents

        by_type = [
            TypeBreakdown(type=t, total_cents=type_totals[t], count=type_counts[t]) for t in sorted(type_totals)
        ]

        months = sorted(set(month_credits) | set(month_debits))
        by_month = [
            MonthlyBreakdown(
                month=m,
                credits_cents=month_credits[m],
                debits_cents=month_debits[m],
                net_cents=month_credits[m] - month_debits[m],
            )
            for m in months
        ]

        return AnalyticsSummary(
            start_date=start_date,
            end_date=end_date,
            total_credits_cents=total_credits,
            total_debits_cents=total_debits,
            net_cents=total_credits - total_debits,
            by_type=by_type,
            by_month=by_month,
        )
