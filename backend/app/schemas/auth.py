from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TwoFARequiredResponse(BaseModel):
    two_fa_required: bool = True
    two_fa_token: str


class TwoFAVerifyRequest(BaseModel):
    two_fa_token: str
    code: str = Field(min_length=6, max_length=6)


class RefreshRequest(BaseModel):
    refresh_token: str


class TwoFASetupResponse(BaseModel):
    secret: str
    otpauth_url: str
    qr_code_base64: str


class TwoFAEnableRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class TwoFAEnableResponse(BaseModel):
    enabled: bool = True
