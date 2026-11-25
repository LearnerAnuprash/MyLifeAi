"""GraphQL context management."""
from typing import Dict, Any, Optional
from strawberry.fastapi import BaseContext
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_context
from app.core.config import get_settings
from app.services.auth import AuthService


class GraphQLContext(BaseContext):
    """GraphQL context with database session and user."""

    def __init__(self, request: Request):
        self.request = request
        self._db: Optional[AsyncSession] = None
        self._user: Optional[Any] = None
        self._settings = get_settings()

    @property
    def db(self) -> AsyncSession:
        """Get database session (lazy initialization)."""
        if self._db is None:
            raise RuntimeError("Database session not initialized. Use get_context() dependency.")
        return self._db

    @property
    def user(self) -> Optional[Any]:
        """Get authenticated user."""
        return self._user

    @property
    def settings(self):
        """Get application settings."""
        return self._settings


async def get_context(request: Request) -> Dict[str, Any]:
    """Create GraphQL context for each request."""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    token = None
    refresh_token = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]

    # Also check for refresh token in header
    refresh_header = request.headers.get("X-Refresh-Token")
    if refresh_header:
        refresh_token = refresh_header

    # Create database session
    async with get_db_context() as db:
        # Create context
        context = GraphQLContext(request)
        context._db = db

        # Authenticate user if token present
        if token:
            auth_service = AuthService(db)
            user = await auth_service.get_user_from_token(token)
            if user:
                context._user = user

        # Store refresh token for mutations that need it
        context.request.state.refresh_token = refresh_token

        yield {
            "request": request,
            "db": db,
            "user": context._user,
            "refresh_token": refresh_token,
            "settings": context._settings,
        }