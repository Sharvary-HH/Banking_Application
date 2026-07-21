from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Banking API"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/banking"
    test_database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/banking_test"

    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-in-.env-this-is-not-secure"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    two_fa_token_expire_minutes: int = 5

    totp_issuer: str = "BankingApp"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    rate_limit_login: str = "5/minute"
    rate_limit_register: str = "5/minute"


settings = Settings()
