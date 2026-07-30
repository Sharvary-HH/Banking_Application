import uuid
from datetime import datetime, timezone

from app.models.loan import Loan
from app.models.transaction import Transaction, TransactionType
from app.services.email_service import (
    deposit_email,
    loan_disbursement_email,
    send_email,
    transfer_email,
    withdrawal_email,
)


def _tx(**overrides) -> Transaction:
    defaults = dict(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        related_account_id=None,
        type=TransactionType.DEPOSIT.value,
        amount_cents=150000,
        balance_after_cents=250000,
        reference_id=uuid.uuid4(),
        description=None,
        created_at=datetime(2026, 3, 15, 14, 30, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return Transaction(**defaults)


def test_deposit_email_contains_amount_and_balance():
    tx = _tx(amount_cents=150000, balance_after_cents=250000)
    subject, html = deposit_email(tx)
    assert "$1,500.00" in subject
    assert "$1,500.00" in html
    assert "$2,500.00" in html


def test_withdrawal_email_contains_amount_and_balance():
    tx = _tx(type=TransactionType.WITHDRAW.value, amount_cents=5000, balance_after_cents=95000)
    subject, html = withdrawal_email(tx)
    assert "$50.00" in subject
    assert "$950.00" in html


def test_transfer_email_uses_debit_leg():
    tx = _tx(type=TransactionType.TRANSFER_OUT.value, amount_cents=20000, balance_after_cents=80000)
    subject, html = transfer_email(tx)
    assert "$200.00" in subject
    assert "$800.00" in html


def test_loan_disbursement_email_contains_principal_and_emi():
    tx = _tx(type=TransactionType.LOAN_DISBURSEMENT.value, amount_cents=1_000_000, balance_after_cents=1_250000)
    loan = Loan(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        disbursement_account_id=uuid.uuid4(),
        principal_cents=1_000_000,
        annual_interest_rate_bps=1200,
        term_months=12,
        emi_cents=88849,
        status="approved",
    )
    subject, html = loan_disbursement_email(tx, loan)
    assert "$10,000.00" in subject
    assert "12 months" in html
    assert "12.00%" in html
    assert "$888.49" in html


async def test_send_email_without_api_key_configured_does_not_raise():
    # RESEND_API_KEY is never set in the test environment, so this exercises the
    # log-only fallback path and must not attempt a real network call.
    await send_email("someone@example.com", "Test subject", "<p>body</p>")
