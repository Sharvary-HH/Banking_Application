import calendar
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.base import AsyncSessionLocal
from app.models.scheduled_transfer import ScheduledTransfer, TransferFrequency
from app.repositories.scheduled_transfer_repo import ScheduledTransferRepository
from app.repositories.user_repo import UserRepository
from app.services.email_service import send_email, transfer_email
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

FAILURE_BACKOFF = timedelta(hours=1)


def _add_months(dt: datetime, months: int) -> datetime:
    total_month_index = dt.month - 1 + months
    year = dt.year + total_month_index // 12
    month = total_month_index % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def _advance_after_success(row: ScheduledTransfer) -> None:
    if row.frequency == TransferFrequency.ONCE.value:
        row.is_active = False
        return
    if row.frequency == TransferFrequency.DAILY.value:
        row.next_run_at = row.next_run_at + timedelta(days=1)
    elif row.frequency == TransferFrequency.WEEKLY.value:
        row.next_run_at = row.next_run_at + timedelta(days=7)
    elif row.frequency == TransferFrequency.MONTHLY.value:
        row.next_run_at = _add_months(row.next_run_at, 1)

    if row.end_date is not None and row.next_run_at > row.end_date:
        row.is_active = False


async def run_due_scheduled_transfers(sessionmaker: async_sessionmaker = AsyncSessionLocal) -> int:
    """Executes every scheduled transfer whose next_run_at has passed, reusing the same
    row-locked TransactionService.transfer() manual transfers use. Returns the number of
    due rows processed (success or failure)."""
    now = datetime.now(timezone.utc)
    processed = 0

    async with sessionmaker() as db:
        due = await ScheduledTransferRepository(db).list_due(now)

        for row in due:
            processed += 1
            # Captured up front: after a rollback below, touching an expired ORM
            # attribute would trigger an implicit lazy-reload, which AsyncSession
            # doesn't support outside an explicit await (raises MissingGreenlet).
            row_id = row.id
            row_user_id = row.user_id
            row_next_run_at = row.next_run_at

            try:
                result = await TransactionService(db).transfer(
                    row_user_id,
                    row.from_account_id,
                    row.to_account_id,
                    row.amount_cents,
                    row.description or "Scheduled transfer",
                )
                row.last_run_status = "success"
                row.last_run_at = now
                _advance_after_success(row)
                await db.commit()

                user = await UserRepository(db).get_by_id(row_user_id)
                if user is not None:
                    subject, html = transfer_email(result.debit)
                    await send_email(user.email, subject, html)
            except Exception:
                logger.exception("Scheduled transfer %s failed", row_id)
                await db.rollback()
                fresh = await db.get(ScheduledTransfer, row_id)
                fresh.last_run_status = "failed"
                fresh.last_run_at = now
                fresh.next_run_at = row_next_run_at + FAILURE_BACKOFF
                await db.commit()

    return processed
