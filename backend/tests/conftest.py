"""Shared pytest configuration and database fixtures."""
import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://mylife:mylife@localhost:55432/mylife_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-at-least-32-chars")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "false")

import pytest_asyncio  # noqa: E402

from app import models  # noqa: E402,F401
from app.db.session import Base, async_session_maker, engine  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def reset_database():
    """Create a fresh schema for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    """Provide a database session for a test."""
    async with async_session_maker() as session:
        yield session
