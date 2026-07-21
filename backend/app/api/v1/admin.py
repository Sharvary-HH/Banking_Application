import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.audit_log_repo import AuditLogRepository
from app.repositories.user_repo import UserRepository
from app.schemas.loan import AdminLoanOut, LoanOut
from app.schemas.user import UserOut
from app.services.loan_service import LoanService

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    return await UserRepository(db).list_all()


@router.get("/loans", response_model=list[AdminLoanOut])
async def list_all_loans(status: str | None = None, db: AsyncSession = Depends(get_db)):
    return await LoanService(db).list_all_for_admin(status)


@router.post("/loans/{loan_id}/approve", response_model=LoanOut)
async def approve_loan(
    loan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await LoanService(db).approve(loan_id, current_user.id)


@router.post("/loans/{loan_id}/reject", response_model=LoanOut)
async def reject_loan(
    loan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await LoanService(db).reject(loan_id, current_user.id)


@router.get("/audit-logs")
async def list_audit_logs(db: AsyncSession = Depends(get_db)):
    logs = await AuditLogRepository(db).list_all()
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "extra_data": log.extra_data,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
