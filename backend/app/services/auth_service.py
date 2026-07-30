import base64
import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO

import qrcode
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    create_two_fa_token,
    decode_token,
    generate_totp_secret,
    get_totp_uri,
    hash_password,
    hash_token,
    verify_password,
    verify_totp_code,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.repositories.audit_log_repo import AuditLogRepository
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse, TwoFARequiredResponse, TwoFASetupResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.audit_logs = AuditLogRepository(db)

    async def register(self, email: str, password: str) -> User:
        existing = await self.users.get_by_email(email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user = User(email=email, hashed_password=hash_password(password), role=UserRole.CUSTOMER.value)
        await self.users.create(user)
        await self.audit_logs.create(user_id=user.id, action="user_registered", entity_type="user", entity_id=str(user.id))
        await self.db.commit()
        return user

    async def login(self, email: str, password: str) -> TokenResponse | TwoFARequiredResponse:
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is disabled")

        if user.totp_enabled:
            return TwoFARequiredResponse(two_fa_token=create_two_fa_token(str(user.id)))

        return await self._issue_tokens(user)

    async def verify_two_fa_login(self, two_fa_token: str, code: str) -> TokenResponse:
        try:
            payload = decode_token(two_fa_token, TokenType.TWO_FA)
            user_id = uuid.UUID(payload["sub"])
        except (ValueError, KeyError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired 2FA token")

        user = await self.users.get_by_id(user_id)
        if user is None or not user.totp_enabled or not user.totp_secret:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="2FA not enabled for this account")

        if not verify_totp_code(user.totp_secret, code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")

        return await self._issue_tokens(user)

    async def refresh(self, raw_refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(raw_refresh_token, TokenType.REFRESH)
            user_id = uuid.UUID(payload["sub"])
        except (ValueError, KeyError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

        token_hash = hash_token(raw_refresh_token)
        stored = await self.refresh_tokens.get_by_hash(token_hash)
        if stored is None or stored.revoked or stored.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")
        if stored.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        # Rotate: revoke the used token so it can never be replayed.
        await self.refresh_tokens.revoke(stored)

        user = await self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        tokens = await self._issue_tokens(user)
        return tokens

    async def setup_two_fa(self, user: User) -> TwoFASetupResponse:
        secret = generate_totp_secret()
        user.totp_secret = secret
        user.totp_enabled = False
        await self.db.flush()
        await self.db.commit()

        otpauth_url = get_totp_uri(secret, user.email)
        qr_img = qrcode.make(otpauth_url)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return TwoFASetupResponse(secret=secret, otpauth_url=otpauth_url, qr_code_base64=qr_base64)

    async def enable_two_fa(self, user: User, code: str) -> None:
        if not user.totp_secret:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Call /2fa/setup first")
        if not verify_totp_code(user.totp_secret, code):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")

        user.totp_enabled = True
        await self.audit_logs.create(user_id=user.id, action="2fa_enabled", entity_type="user", entity_id=str(user.id))
        await self.db.commit()

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(str(user.id), user.role)
        refresh_token_raw = create_refresh_token(str(user.id))

        refresh_payload = decode_token(refresh_token_raw, TokenType.REFRESH)
        expires_at = datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)

        await self.refresh_tokens.create(
            RefreshToken(user_id=user.id, token_hash=hash_token(refresh_token_raw), expires_at=expires_at)
        )
        await self.audit_logs.create(user_id=user.id, action="login", entity_type="user", entity_id=str(user.id))
        await self.db.commit()

        return TokenResponse(access_token=access_token, refresh_token=refresh_token_raw)
