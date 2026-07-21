import logging

import httpx

from app.core.config import settings
from app.models.loan import Loan
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def _format_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    return f"{sign}${abs(cents) / 100:,.2f}"


async def send_email(to: str, subject: str, html_body: str) -> None:
    """Never raises — a failed or unconfigured email must never fail the transaction
    that triggered it. Logs instead of sending when RESEND_API_KEY isn't set, which is
    the default everywhere (local dev, tests, a fresh deploy) so the feature is visibly
    working in `docker compose logs` without requiring anyone to sign up for anything."""
    if not settings.resend_api_key:
        logger.info("EMAIL (no provider configured) to=%s subject=%r", to, subject)
        return

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                RESEND_URL,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={"from": settings.email_from, "to": [to], "subject": subject, "html": html_body},
            )
            resp.raise_for_status()
    except Exception:
        logger.exception("Failed to send email to=%s subject=%r", to, subject)


def deposit_email(tx: Transaction) -> tuple[str, str]:
    subject = f"Deposit received: {_format_cents(tx.amount_cents)}"
    html = (
        f"<p>A deposit of <strong>{_format_cents(tx.amount_cents)}</strong> was made to your account.</p>"
        f"<p>New balance: <strong>{_format_cents(tx.balance_after_cents)}</strong></p>"
        f"<p>{tx.created_at:%b %d, %Y %I:%M %p} UTC</p>"
    )
    return subject, html


def withdrawal_email(tx: Transaction) -> tuple[str, str]:
    subject = f"Withdrawal: {_format_cents(tx.amount_cents)}"
    html = (
        f"<p>A withdrawal of <strong>{_format_cents(tx.amount_cents)}</strong> was made from your account.</p>"
        f"<p>New balance: <strong>{_format_cents(tx.balance_after_cents)}</strong></p>"
        f"<p>{tx.created_at:%b %d, %Y %I:%M %p} UTC</p>"
    )
    return subject, html


def transfer_email(debit_tx: Transaction) -> tuple[str, str]:
    subject = f"Transfer sent: {_format_cents(debit_tx.amount_cents)}"
    html = (
        f"<p>A transfer of <strong>{_format_cents(debit_tx.amount_cents)}</strong> was sent from your account.</p>"
        f"<p>New balance: <strong>{_format_cents(debit_tx.balance_after_cents)}</strong></p>"
        f"<p>{debit_tx.created_at:%b %d, %Y %I:%M %p} UTC</p>"
    )
    return subject, html


def loan_disbursement_email(tx: Transaction, loan: Loan) -> tuple[str, str]:
    subject = f"Loan approved: {_format_cents(loan.principal_cents)} disbursed"
    html = (
        f"<p>Your loan application was approved. <strong>{_format_cents(loan.principal_cents)}</strong> "
        f"has been disbursed to your account.</p>"
        f"<p>Term: {loan.term_months} months at {loan.annual_interest_rate_bps / 100:.2f}% APR — "
        f"monthly payment (EMI): <strong>{_format_cents(loan.emi_cents)}</strong></p>"
        f"<p>New balance: <strong>{_format_cents(tx.balance_after_cents)}</strong></p>"
    )
    return subject, html
