"""Database session management."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional, request-scoped database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create tables from metadata.

    Development bootstrap only. Production deployments must run
    ``alembic upgrade head`` instead (see docker-compose/Dockerfile).
    """
    if not settings.is_development:
        return

    from app.models import (  # noqa: F401 - imported for metadata registration
        Category,
        Conversation,
        Event,
        EventReminder,
        Message,
        Notification,
        User,
        UserMemory,
        UserSettings,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
