from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def build_engine(database_url: str):
    return create_async_engine(database_url, pool_pre_ping=True)


def build_sessionmaker(bound_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=bound_engine, expire_on_commit=False, autoflush=False)
