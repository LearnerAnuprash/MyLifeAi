"""GraphQL Event types."""
import strawberry
from typing import Optional, List
from datetime import datetime
import uuid
from app.graphql.types.scalars import DateTime, UUID
from app.graphql.types.enums import EventStatus, EventPriority, NotificationType
from app.graphql.types.category import Category


@strawberry.type
class EventReminder:
    """Event reminder GraphQL type."""
    id: UUID
    event_id: UUID
    user_id: UUID
    minutes_before: int
    notification_type: NotificationType
    is_sent: bool
    sent_at: Optional[DateTime]
    created_at: DateTime


@strawberry.type
class Event:
    """Event GraphQL type."""
    id: UUID
    user_id: UUID
    category: Optional[Category]
    title: str
    description: Optional[str]
    location: Optional[str]
    start_time: DateTime
    end_time: DateTime
    all_day: bool
    timezone: str
    priority: EventPriority
    status: EventStatus
    is_recurring: bool
    rrule: Optional[str]
    rrule_original_start: Optional[DateTime]
    recurrence_exceptions: List[DateTime]
    preparation_notes: Optional[str]
    completed_at: Optional[DateTime]
    created_at: DateTime
    updated_at: DateTime
    reminders: List[EventReminder]


@strawberry.type
class PageInfo:
    """Pagination page info."""
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str]
    end_cursor: Optional[str]


@strawberry.type
class EventEdge:
    """Event edge for pagination."""
    node: Event
    cursor: str


@strawberry.type
class EventConnection:
    """Event connection for pagination."""
    edges: List[EventEdge]
    page_info: PageInfo
    total_count: int