import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.repositories.account_repo import AccountRepository
from app.repositories.audit_log_repo import AuditLogRepository
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.transaction import PaginatedTransactions, TransactionOut, TransferResponse


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.accounts = AccountRepository(db)
        self.transactions = TransactionRepository(db)
        self.audit_logs = AuditLogRepository(db)

    async def deposit(self, user_id: uuid.UUID, account_id: uuid.UUID, amount_cents: int, description: str | None) -> Transaction:
        account = await self.accounts.get_owned_locked(account_id, user_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        account.balance_cents += amount_cents
        account.version += 1

        tx = await self.transactions.create(
            Transaction(
                account_id=account.id,
                related_account_id=None,
                type=TransactionType.DEPOSIT.value,
                amount_cents=amount_cents,
                balance_after_cents=account.balance_cents,
                description=description,
            )
        )
        await self.audit_logs.create(
            user_id=user_id,
            action="deposit",
            entity_type="account",
            entity_id=str(account.id),
            extra_data={"amount_cents": amount_cents, "transaction_id": str(tx.id)},
        )
        await self.db.commit()
        return tx

    async def withdraw(self, user_id: uuid.UUID, account_id: uuid.UUID, amount_cents: int, description: str | None) -> Transaction:
        account = await self.accounts.get_owned_locked(account_id, user_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        if account.balance_cents < amount_cents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")

        account.balance_cents -= amount_cents
        account.version += 1

        tx = await self.transactions.create(
            Transaction(
                account_id=account.id,
                related_account_id=None,
                type=TransactionType.WITHDRAW.value,
                amount_cents=amount_cents,
                balance_after_cents=account.balance_cents,
                description=description,
            )
        )
        await self.audit_logs.create(
            user_id=user_id,
            action="withdraw",
            entity_type="account",
            entity_id=str(account.id),
            extra_data={"amount_cents": amount_cents, "transaction_id": str(tx.id)},
        )
        await self.db.commit()
        return tx

    async def transfer(
        self,
        user_id: uuid.UUID,
        from_account_id: uuid.UUID,
        to_account_id: uuid.UUID,
        amount_cents: int,
        description: str | None,
    ) -> TransferResponse:
        if from_account_id == to_account_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot transfer to the same account")

        # Always lock accounts in a fixed (sorted) order regardless of transfer direction,
        # so two concurrent opposite-direction transfers between the same pair of accounts
        # can never deadlock against each other.
        ordered_ids = sorted([from_account_id, to_account_id], key=lambda u: u.hex)
        locked: dict[uuid.UUID, Account] = {}
        for account_id in ordered_ids:
            account = await self.accounts.get_locked(account_id)
            if account is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
            locked[account_id] = account

        from_account = locked[from_account_id]
        to_account = locked[to_account_id]

        if from_account.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        if from_account.balance_cents < amount_cents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")

        reference_id = uuid.uuid4()

        from_account.balance_cents -= amount_cents
        from_account.version += 1
        to_account.balance_cents += amount_cents
        to_account.version += 1

        debit_tx = await self.transactions.create(
            Transaction(
                account_id=from_account.id,
                related_account_id=to_account.id,
                type=TransactionType.TRANSFER_OUT.value,
                amount_cents=amount_cents,
                balance_after_cents=from_account.balance_cents,
                reference_id=reference_id,
                description=description,
            )
        )
        credit_tx = await self.transactions.create(
            Transaction(
                account_id=to_account.id,
                related_account_id=from_account.id,
                type=TransactionType.TRANSFER_IN.value,
                amount_cents=amount_cents,
                balance_after_cents=to_account.balance_cents,
                reference_id=reference_id,
                description=description,
            )
        )

        await self.audit_logs.create(
            user_id=user_id,
            action="transfer",
            entity_type="account",
            entity_id=str(from_account.id),
            extra_data={
                "amount_cents": amount_cents,
                "to_account_id": str(to_account.id),
                "reference_id": str(reference_id),
            },
        )
        await self.db.commit()
        return TransferResponse(debit=TransactionOut.model_validate(debit_tx), credit=TransactionOut.model_validate(credit_tx))

    async def list_transactions(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
        *,
        type_filter: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
        min_amount_cents: int | None,
        max_amount_cents: int | None,
        page: int,
        page_size: int,
    ) -> PaginatedTransactions:
        account = await self.accounts.get_owned_by_user(account_id, user_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        items, total = await self.transactions.list_for_account(
            account_id,
            type_filter=type_filter,
            start_date=start_date,
            end_date=end_date,
            min_amount_cents=min_amount_cents,
            max_amount_cents=max_amount_cents,
            page=page,
            page_size=page_size,
        )
        return PaginatedTransactions(
            items=[TransactionOut.model_validate(t) for t in items],
            total=total,
            page=page,
            page_size=page_size,
        )
