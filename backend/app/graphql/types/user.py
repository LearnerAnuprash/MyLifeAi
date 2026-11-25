"""GraphQL User types."""
import strawberry
from typing import Optional, List
from datetime import datetime
import uuid
from app.graphql.types.scalars import DateTime, UUID
from app.graphql.types.enums import Theme, CalendarView


@strawberry.type
class UserSettings:
    """User settings GraphQL type."""
    theme: Theme
    calendar_default_view: CalendarView
    week_start_day: int
    default_reminder_minutes: List[int]
    notification_email: bool
    notification_push: bool
    ai_provider: str
    ai_model: str
    language: str
    date_format: str
    time_format: str


@strawberry.type
class User:
    """User GraphQL type."""
    id: UUID
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    timezone: str
    locale: str
    is_active: bool
    is_verified: bool
    created_at: DateTime
    updated_at: DateTime
    settings: UserSettings