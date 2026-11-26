"""Shared helpers for Celery tasks."""
import asyncio
from typing import Awaitable, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


def run_async(coro: Awaitable[T]) -> T:
    """Run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
