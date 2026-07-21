from fastapi import APIRouter

from app.api.v1 import accounts, admin, auth, beneficiaries, scheduled_transfers, transactions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(accounts.router)
api_router.include_router(transactions.router)
api_router.include_router(beneficiaries.router)
api_router.include_router(scheduled_transfers.router)
api_router.include_router(admin.router)
