"""GraphQL context management."""
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import Request

from app.core.config import get_settings
from app.db.session import get_db
from app.services.auth import AuthService


async def get_context(request: Request) -> AsyncIterator[Dict[str, Any]]:
    """Create the per-request GraphQL context.

    Yields a single request-scoped ``AsyncSession`` that every resolver and
    service shares. The session is committed on success and rolled back on
    failure by :func:`app.db.session.get_db`.
    """
    auth_header = request.headers.get("Authorization")
    token: Optional[str] = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]

    refresh_token = request.headers.get("X-Refresh-Token")

    async with get_db() as db:
        user = None
        if token:
            user = await AuthService(db).get_user_from_token(token)

        yield {
            "request": request,
            "db": db,
            "user": user,
            "refresh_token": refresh_token,
            "settings": get_settings(),
        }
