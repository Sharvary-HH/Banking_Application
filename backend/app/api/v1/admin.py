from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.db.session import get_db
from app.repositories.audit_log_repo import AuditLogRepository
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    return await UserRepository(db).list_all()


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
