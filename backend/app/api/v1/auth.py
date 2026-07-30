from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    TwoFAEnableRequest,
    TwoFAEnableResponse,
    TwoFARequiredResponse,
    TwoFASetupResponse,
    TwoFAVerifyRequest,
)
from app.schemas.user import UserCreate, UserMeOut, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_register)
async def register(request: Request, payload: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.register(payload.email, payload.password)
    return user


@router.post("/login", response_model=TokenResponse | TwoFARequiredResponse)
@limiter.limit(settings.rate_limit_login)
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.login(payload.email, payload.password)


@router.post("/login/verify-2fa", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_login)
async def verify_two_fa(request: Request, payload: TwoFAVerifyRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.verify_two_fa_login(payload.two_fa_token, payload.code)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.refresh(payload.refresh_token)


@router.get("/me", response_model=UserMeOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/2fa/setup", response_model=TwoFASetupResponse)
async def setup_two_fa(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = AuthService(db)
    return await service.setup_two_fa(current_user)


@router.post("/2fa/enable", response_model=TwoFAEnableResponse)
async def enable_two_fa(
    payload: TwoFAEnableRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AuthService(db)
    await service.enable_two_fa(current_user, payload.code)
    return TwoFAEnableResponse()
