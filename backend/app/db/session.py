"""Database session management."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings
from sqlalchemy import text

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
    """Dependency for getting database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for getting database session outside of FastAPI dependencies."""
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
    """Initialize database - create all tables."""
    print("DEBUG: Creating database tables...")
    # Import models to register them with Base.metadata
    from app.models import User, Category, Event, EventReminder, Conversation, Message, UserMemory, Notification, UserSettings
    print(f"DEBUG: Tables in metadata: {list(Base.metadata.tables.keys())}")
    try:
        # Use engine.begin() for proper transaction management with automatic commit
        async with engine.begin() as conn:
            try:
                await conn.run_sync(Base.metadata.create_all, checkfirst=True)
                print("DEBUG: Database tables created successfully!")
                # Verify tables exist after creation
                from sqlalchemy import text
                result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                tables = result.fetchall()
                print(f"DEBUG: Tables in database after creation: {[t[0] for t in tables]}")
            except Exception as e:
                error_str = str(e)
                if "already exists" in error_str:
                    print(f"DEBUG: Tables already exist, continuing: {e}")
                else:
                    raise
    except Exception as e:
        if "already exists" in str(e):
            print(f"DEBUG: Tables already exist, skipping creation: {e}")
        else:
            raise


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()