import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan import Loan, LoanStatus
from app.repositories.account_repo import AccountRepository
from app.repositories.audit_log_repo import AuditLogRepository
from app.repositories.loan_repo import LoanRepository
from app.repositories.user_repo import UserRepository
from app.schemas.loan import AdminLoanOut, EmiCalculationResponse
from app.services.emi import calculate_emi
from app.services.transaction_service import TransactionService


class LoanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.loans = LoanRepository(db)
        self.accounts = AccountRepository(db)
        self.users = UserRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def calculate_emi(self, principal_cents: int, annual_interest_rate_bps: int, term_months: int) -> EmiCalculationResponse:
        breakdown = calculate_emi(principal_cents, annual_interest_rate_bps, term_months)
        return EmiCalculationResponse(
            emi_cents=breakdown.emi_cents,
            total_payment_cents=breakdown.total_payment_cents,
            total_interest_cents=breakdown.total_interest_cents,
        )

    async def apply(
        self,
        user_id: uuid.UUID,
        disbursement_account_id: uuid.UUID,
        principal_cents: int,
        annual_interest_rate_bps: int,
        term_months: int,
    ) -> Loan:
        account = await self.accounts.get_owned_by_user(disbursement_account_id, user_id)
        if account is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        breakdown = calculate_emi(principal_cents, annual_interest_rate_bps, term_months)

        loan = await self.loans.create(
            Loan(
                user_id=user_id,
                disbursement_account_id=disbursement_account_id,
                principal_cents=principal_cents,
                annual_interest_rate_bps=annual_interest_rate_bps,
                term_months=term_months,
                emi_cents=breakdown.emi_cents,
                status=LoanStatus.PENDING.value,
            )
        )
        await self.audit_logs.create(
            user_id=user_id,
            action="loan_applied",
            entity_type="loan",
            entity_id=str(loan.id),
            extra_data={"principal_cents": principal_cents, "term_months": term_months},
        )
        await self.db.commit()
        return loan

    async def list_for_user(self, user_id: uuid.UUID) -> list[Loan]:
        return await self.loans.list_for_user(user_id)

    async def get_owned_or_404(self, loan_id: uuid.UUID, user_id: uuid.UUID) -> Loan:
        loan = await self.loans.get_owned_by_user(loan_id, user_id)
        if loan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
        return loan

    async def list_all_for_admin(self, status_filter: str | None) -> list[AdminLoanOut]:
        loans = await self.loans.list_all(status_filter)
        out = []
        for loan in loans:
            applicant = await self.users.get_by_id(loan.user_id)
            out.append(
                AdminLoanOut(
                    id=loan.id,
                    user_id=loan.user_id,
                    applicant_email=applicant.email if applicant else "unknown",
                    disbursement_account_id=loan.disbursement_account_id,
                    principal_cents=loan.principal_cents,
                    annual_interest_rate_bps=loan.annual_interest_rate_bps,
                    term_months=loan.term_months,
                    emi_cents=loan.emi_cents,
                    status=loan.status,
                    decided_at=loan.decided_at,
                    created_at=loan.created_at,
                )
            )
        return out

    async def approve(self, loan_id: uuid.UUID, admin_user_id: uuid.UUID) -> Loan:
        loan = await self._get_pending_or_404(loan_id)

        await TransactionService(self.db).loan_disbursement(
            loan.disbursement_account_id,
            loan.user_id,
            loan.principal_cents,
            f"Loan disbursement ({loan.term_months}mo @ {loan.annual_interest_rate_bps / 100:.2f}% APR)",
        )

        loan.status = LoanStatus.APPROVED.value
        loan.decided_at = datetime.now(timezone.utc)
        loan.decided_by_user_id = admin_user_id
        await self.audit_logs.create(
            user_id=admin_user_id,
            action="loan_approved",
            entity_type="loan",
            entity_id=str(loan.id),
            extra_data={"applicant_user_id": str(loan.user_id), "principal_cents": loan.principal_cents},
        )
        await self.db.commit()
        return loan

    async def reject(self, loan_id: uuid.UUID, admin_user_id: uuid.UUID) -> Loan:
        loan = await self._get_pending_or_404(loan_id)

        loan.status = LoanStatus.REJECTED.value
        loan.decided_at = datetime.now(timezone.utc)
        loan.decided_by_user_id = admin_user_id
        await self.audit_logs.create(
            user_id=admin_user_id,
            action="loan_rejected",
            entity_type="loan",
            entity_id=str(loan.id),
            extra_data={"applicant_user_id": str(loan.user_id)},
        )
        await self.db.commit()
        return loan

    async def _get_pending_or_404(self, loan_id: uuid.UUID) -> Loan:
        loan = await self.loans.get_by_id(loan_id)
        if loan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
        if loan.status != LoanStatus.PENDING.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Loan is not pending")
        return loan
