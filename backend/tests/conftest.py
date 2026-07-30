import os
import uuid
from collections.abc import AsyncGenerator

# Must run before any `app.*` import: the login/register rate limits are baked into the
# route decorators at import time, and the default 5/minute would make the test suite
# itself trip the brute-force guard it's supposed to be testing around.
os.environ["RATE_LIMIT_LOGIN"] = "10000/minute"
os.environ["RATE_LIMIT_REGISTER"] = "10000/minute"
# Prevents the APScheduler background job (app/main.py's lifespan) from starting and
# polling the dev DB during test runs — see app/core/scheduler.py.
os.environ["ENVIRONMENT"] = "test"

import pytest
import pytest_asyncio
import redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import settings
from app.db.base import Base, build_engine, build_sessionmaker
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _flush_rate_limit_storage():
    redis.from_url(settings.redis_url).flushdb()


@pytest_asyncio.fixture
async def db_sessionmaker() -> AsyncGenerator[async_sessionmaker, None]:
    # A fresh engine per test, bound to that test's own event loop — reusing one engine
    # across pytest-asyncio's per-test loops leaves pooled asyncpg connections attached
    # to a closed loop and breaks the next test.
    engine = build_engine(settings.test_database_url)
    sessionmaker = build_sessionmaker(engine)

    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    yield sessionmaker
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_sessionmaker: async_sessionmaker) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator:
        async with db_sessionmaker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


def unique_email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


async def register_and_login(client: AsyncClient, email: str | None = None, password: str = "password123") -> dict:
    email = email or unique_email()
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    body = resp.json()
    return {"email": email, "password": password, **body}


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def promote_to_admin(db_sessionmaker: async_sessionmaker, email: str) -> None:
    """Flips a registered user's role to admin directly in the DB (there's no
    self-service escalation endpoint by design). get_current_user re-fetches the user
    from the DB on every request rather than trusting the JWT's role claim, so the
    caller's existing access token starts working for admin routes immediately."""
    from app.models.user import User

    async with db_sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.role = "admin"
        await session.commit()
