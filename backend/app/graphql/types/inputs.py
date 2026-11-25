"""GraphQL input types."""
import strawberry
from typing import Optional, List
from datetime import datetime
import uuid
from app.graphql.types.scalars import DateTime, UUID
from app.graphql.types.enums import (
    EventStatus,
    EventPriority,
    NotificationType,
    MemoryType,
    NotificationCategory,
    CalendarView,
    Theme,
)


# Auth inputs
@strawberry.input
class RegisterInput:
    email: str
    password: str
    full_name: Optional[str] = None


@strawberry.input
class LoginInput:
    email: str
    password: str


# Category inputs
@strawberry.input
class CreateCategoryInput:
    parent_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    color: str
    icon: Optional[str] = None
    default_reminder_minutes: Optional[List[int]] = None


@strawberry.input
class UpdateCategoryInput:
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    default_reminder_minutes: Optional[List[int]] = None
    sort_order: Optional[int] = None


# Event inputs
@strawberry.input
class CreateEventReminderInput:
    minutes_before: int
    notification_type: NotificationType = NotificationType.IN_APP


@strawberry.input
class CreateEventInput:
    category_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: DateTime
    end_time: DateTime
    all_day: bool = False
    timezone: str
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.SCHEDULED
    is_recurring: bool = False
    rrule: Optional[str] = None
    preparation_notes: Optional[str] = None
    reminders: Optional[List[CreateEventReminderInput]] = None


@strawberry.input
class UpdateEventInput:
    category_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[DateTime] = None
    end_time: Optional[DateTime] = None
    all_day: Optional[bool] = None
    timezone: Optional[str] = None
    priority: Optional[EventPriority] = None
    status: Optional[EventStatus] = None
    preparation_notes: Optional[str] = None


@strawberry.input
class EventFilterInput:
    category_ids: Optional[List[UUID]] = None
    statuses: Optional[List[EventStatus]] = None
    priorities: Optional[List[EventPriority]] = None
    start_date: Optional[DateTime] = None
    end_date: Optional[DateTime] = None
    search_query: Optional[str] = None
    is_recurring: Optional[bool] = None


# Conversation inputs
@strawberry.input
class CreateConversationInput:
    title: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None


@strawberry.input
class SendMessageInput:
    conversation_id: UUID
    content: str


# Memory inputs
@strawberry.input
class CreateMemoryInput:
    memory_type: MemoryType
    title: str
    content: str
    source_conversation_id: Optional[UUID] = None
    confidence: Optional[float] = 1.0


@strawberry.input
class UpdateMemoryInput:
    title: Optional[str] = None
    content: Optional[str] = None
    memory_type: Optional[MemoryType] = None
    confidence: Optional[float] = None
    is_active: Optional[bool] = None


@strawberry.input
class MemorySearchInput:
    query: str
    memory_types: Optional[List[MemoryType]] = None
    limit: Optional[int] = 10
    threshold: Optional[float] = 0.7


@strawberry.input
class MemoryFilterInput:
    memory_types: Optional[List[MemoryType]] = None
    is_active: Optional[bool] = None


# Settings inputs
@strawberry.input
class UpdateSettingsInput:
    theme: Optional[Theme] = None
    calendar_default_view: Optional[CalendarView] = None
    week_start_day: Optional[int] = None
    default_reminder_minutes: Optional[List[int]] = None
    notification_email: Optional[bool] = None
    notification_push: Optional[bool] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    language: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None


# Calendar inputs
@strawberry.input
class CalendarRangeInput:
    start_date: DateTime
    end_date: DateTime
    view: CalendarView
    timezone: str


# AI Planner inputs
@strawberry.input
class AIEventProposalInput:
    title: str
    description: Optional[str] = None
    suggested_dates: List[DateTime]
    duration_minutes: int
    category_id: Optional[UUID] = None
    priority: EventPriority = EventPriority.NORMAL
    preparation_notes: Optional[str] = None
    reminders: Optional[List[CreateEventReminderInput]] = None


@strawberry.input
class BulkUpdateEventInput:
    id: UUID
    input: UpdateEventInput


@strawberry.input
class NotificationFilterInput:
    is_read: Optional[bool] = None
    types: Optional[List[NotificationCategory]] = None