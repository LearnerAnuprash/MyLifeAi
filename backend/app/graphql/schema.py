"""GraphQL schema definition."""
import strawberry
from typing import Optional, List, AsyncGenerator
from datetime import datetime
import uuid
from strawberry.types import Info

from app.graphql.types import (
    # Types
    User,
    UserSettings,
    Category,
    CategoryTree,
    Event,
    EventConnection,
    EventEdge,
    PageInfo,
    EventReminder,
    Conversation,
    Message,
    ConversationConnection,
    ConversationEdge,
    UserMemory,
    MemoryConnection,
    MemoryEdge,
    Notification,
    NotificationConnection,
    NotificationEdge,
    # Inputs
    RegisterInput,
    LoginInput,
    CreateCategoryInput,
    UpdateCategoryInput,
    CreateEventInput,
    UpdateEventInput,
    CreateEventReminderInput,
    EventFilterInput,
    CreateConversationInput,
    SendMessageInput,
    CreateMemoryInput,
    UpdateMemoryInput,
    MemorySearchInput,
    MemoryFilterInput,
    UpdateSettingsInput,
    CalendarRangeInput,
    AIEventProposalInput,
    BulkUpdateEventInput,
    NotificationFilterInput,
    # Payloads
    AuthPayload,
    SendMessagePayload,
    ProposedEvent,
    MutationResult,
    Success,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    # Enums
    EventStatus,
    EventPriority,
    NotificationType,
    ConversationRole,
    MemoryType,
    NotificationCategory,
    CalendarView,
    Theme,
)
from app.graphql.types.scalars import DateTime, UUID, JSON


# Context type
from app.core.config import Settings


@strawberry.type
class Query:
    """GraphQL queries."""

    @strawberry.field
    async def me(self, info: Info) -> Optional[User]:
        """Get current authenticated user."""
        user = info.context.get("user")
        if not user:
            return None
        return await user.to_gql()

    # Categories
    @strawberry.field
    async def categories(self, info: Info) -> CategoryTree:
        """Get user's category tree."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_category_tree()

    @strawberry.field
    async def category(self, info: Info, id: UUID) -> Optional[Category]:
        """Get category by ID."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_category(id)

    # Events
    @strawberry.field
    async def events(
        self,
        info: Info,
        filter: Optional[EventFilterInput] = None,
        first: Optional[int] = 20,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
    ) -> EventConnection:
        """Get paginated events with filtering."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_events(filter, first, after, last, before)

    @strawberry.field
    async def event(self, info: Info, id: UUID) -> Optional[Event]:
        """Get event by ID."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_event(id)

    @strawberry.field
    async def upcoming_events(
        self,
        info: Info,
        limit: int = 10,
        days: int = 30,
    ) -> List[Event]:
        """Get upcoming events."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_upcoming_events(limit, days)

    @strawberry.field
    async def past_events(
        self,
        info: Info,
        limit: int = 10,
        days: int = 30,
    ) -> List[Event]:
        """Get past events."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_past_events(limit, days)

    @strawberry.field
    async def events_by_date_range(
        self,
        info: Info,
        range: CalendarRangeInput,
    ) -> List[Event]:
        """Get events within a date range for calendar views."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_events_by_date_range(range)

    @strawberry.field
    async def recurring_event_instances(
        self,
        info: Info,
        event_id: UUID,
        range: CalendarRangeInput,
    ) -> List[Event]:
        """Get recurring event instances within a range."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_recurring_instances(event_id, range)

    # Conversations
    @strawberry.field
    async def conversations(
        self,
        info: Info,
        first: int = 20,
        after: Optional[str] = None,
    ) -> ConversationConnection:
        """Get user's conversations."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_conversations(first, after)

    @strawberry.field
    async def conversation(self, info: Info, id: UUID) -> Optional[Conversation]:
        """Get conversation by ID."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_conversation(id)

    # Memory
    @strawberry.field
    async def memories(
        self,
        info: Info,
        filter: Optional[MemoryFilterInput] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> MemoryConnection:
        """Get user's memories."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_memories(filter, first, after)

    @strawberry.field
    async def memory(self, info: Info, id: UUID) -> Optional[UserMemory]:
        """Get memory by ID."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_memory(id)

    @strawberry.field
    async def search_memory(
        self,
        info: Info,
        input: MemorySearchInput,
    ) -> List[UserMemory]:
        """Semantic search for memories."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.search_memory(input)

    # Notifications
    @strawberry.field
    async def notifications(
        self,
        info: Info,
        filter: Optional[NotificationFilterInput] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> NotificationConnection:
        """Get user's notifications."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_notifications(filter, first, after)

    @strawberry.field
    async def unread_notification_count(self, info: Info) -> int:
        """Get count of unread notifications."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_unread_notification_count()

    # Calendar convenience queries
    @strawberry.field
    async def calendar_events(
        self,
        info: Info,
        range: CalendarRangeInput,
    ) -> List[Event]:
        """Get events for calendar view."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_calendar_events(range)

    @strawberry.field
    async def today_events(self, info: Info) -> List[Event]:
        """Get today's events."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_today_events()

    @strawberry.field
    async def this_week_events(self, info: Info) -> List[Event]:
        """Get this week's events."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_this_week_events()

    @strawberry.field
    async def this_month_events(self, info: Info) -> List[Event]:
        """Get this month's events."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.get_this_month_events()


# Need to add NotificationFilterInput
@strawberry.input
class NotificationFilterInput:
    is_read: Optional[bool] = None
    types: Optional[List[NotificationCategory]] = None


@strawberry.type
class Mutation:
    """GraphQL mutations."""

    # Auth
    @strawberry.mutation
    async def register(self, info: Info, input: RegisterInput) -> AuthPayload:
        """Register a new user."""
        from app.services.auth import AuthService
        auth_service = AuthService(info.context["db"])
        return await auth_service.register(input)

    @strawberry.mutation
    async def login(self, info: Info, input: LoginInput) -> AuthPayload:
        """Login user."""
        from app.services.auth import AuthService
        auth_service = AuthService(info.context["db"])
        return await auth_service.login(input)

    @strawberry.mutation
    async def logout(self, info: Info) -> bool:
        """Logout user (invalidate token)."""
        # Token invalidation handled client-side
        return True

    @strawberry.mutation
    async def refresh_token(self, info: Info) -> str:
        """Refresh access token."""
        from app.services.auth import AuthService
        auth_service = AuthService(info.context["db"])
        return await auth_service.refresh_token(info.context.get("refresh_token"))

    @strawberry.mutation
    async def verify_email(self, info: Info, token: str) -> bool:
        """Verify email address."""
        from app.services.auth import AuthService
        auth_service = AuthService(info.context["db"])
        return await auth_service.verify_email(token)

    @strawberry.mutation
    async def request_password_reset(self, info: Info, email: str) -> bool:
        """Request password reset."""
        from app.services.auth import AuthService
        auth_service = AuthService(info.context["db"])
        return await auth_service.request_password_reset(email)

    @strawberry.mutation
    async def reset_password(self, info: Info, token: str, password: str) -> bool:
        """Reset password with token."""
        from app.services.auth import AuthService
        auth_service = AuthService(info.context["db"])
        return await auth_service.reset_password(token, password)

    # Categories
    @strawberry.mutation
    async def create_category(self, info: Info, input: CreateCategoryInput) -> Category:
        """Create a new category."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.create_category(input)

    @strawberry.mutation
    async def update_category(self, info: Info, id: UUID, input: UpdateCategoryInput) -> Category:
        """Update a category."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.update_category(id, input)

    @strawberry.mutation
    async def delete_category(self, info: Info, id: UUID) -> bool:
        """Delete a category."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.delete_category(id)

    @strawberry.mutation
    async def reorder_categories(self, info: Info, category_ids: List[UUID]) -> List[Category]:
        """Reorder categories."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.reorder_categories(category_ids)

    # Events
    @strawberry.mutation
    async def create_event(self, info: Info, input: CreateEventInput) -> Event:
        """Create a new event."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.create_event(input)

    @strawberry.mutation
    async def update_event(self, info: Info, id: UUID, input: UpdateEventInput) -> Event:
        """Update an event."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.update_event(id, input)

    @strawberry.mutation
    async def delete_event(self, info: Info, id: UUID) -> bool:
        """Delete an event."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.delete_event(id)

    @strawberry.mutation
    async def duplicate_event(self, info: Info, id: UUID, new_start_time: DateTime) -> Event:
        """Duplicate an event to a new date."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.duplicate_event(id, new_start_time)

    @strawberry.mutation
    async def complete_event(self, info: Info, id: UUID) -> Event:
        """Mark event as completed."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.complete_event(id)

    @strawberry.mutation
    async def bulk_create_events(self, info: Info, inputs: List[CreateEventInput]) -> List[Event]:
        """Create multiple events."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.bulk_create_events(inputs)

    @strawberry.mutation
    async def bulk_update_events(self, info: Info, inputs: List[BulkUpdateEventInput]) -> List[Event]:
        """Update multiple events."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.bulk_update_events(inputs)

    @strawberry.mutation
    async def bulk_delete_events(self, info: Info, ids: List[UUID]) -> bool:
        """Delete multiple events."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.bulk_delete_events(ids)

    # Recurring events
    @strawberry.mutation
    async def create_recurring_exception(
        self,
        info: Info,
        event_id: UUID,
        exception_date: DateTime,
        input: CreateEventInput,
    ) -> Event:
        """Create an exception for a recurring event."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.create_recurring_exception(event_id, exception_date, input)

    @strawberry.mutation
    async def update_recurring_series(
        self,
        info: Info,
        event_id: UUID,
        input: UpdateEventInput,
    ) -> Event:
        """Update entire recurring series."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.update_recurring_series(event_id, input)

    @strawberry.mutation
    async def delete_recurring_series(
        self,
        info: Info,
        event_id: UUID,
        delete_future: bool = True,
    ) -> bool:
        """Delete recurring series."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.delete_recurring_series(event_id, delete_future)

    # Conversations
    @strawberry.mutation
    async def create_conversation(self, info: Info, input: CreateConversationInput) -> Conversation:
        """Create a new conversation."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.create_conversation(input)

    @strawberry.mutation
    async def update_conversation(self, info: Info, id: UUID, title: Optional[str] = None) -> Conversation:
        """Update conversation title."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.update_conversation(id, title)

    @strawberry.mutation
    async def delete_conversation(self, info: Info, id: UUID) -> bool:
        """Delete a conversation."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.delete_conversation(id)

    @strawberry.mutation
    async def send_message(self, info: Info, input: SendMessageInput) -> SendMessagePayload:
        """Send a message and get AI response."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.send_message(input)

    # Memory
    @strawberry.mutation
    async def create_memory(self, info: Info, input: CreateMemoryInput) -> UserMemory:
        """Create a memory entry."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.create_memory(input)

    @strawberry.mutation
    async def update_memory(self, info: Info, id: UUID, input: UpdateMemoryInput) -> UserMemory:
        """Update a memory entry."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.update_memory(id, input)

    @strawberry.mutation
    async def delete_memory(self, info: Info, id: UUID) -> bool:
        """Delete a memory entry."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.delete_memory(id)

    @strawberry.mutation
    async def bulk_create_memories(self, info: Info, inputs: List[CreateMemoryInput]) -> List[UserMemory]:
        """Create multiple memory entries."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.bulk_create_memories(inputs)

    # Notifications
    @strawberry.mutation
    async def mark_notification_read(self, info: Info, id: UUID) -> Notification:
        """Mark notification as read."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.mark_notification_read(id)

    @strawberry.mutation
    async def mark_all_notifications_read(self, info: Info) -> bool:
        """Mark all notifications as read."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.mark_all_notifications_read()

    @strawberry.mutation
    async def delete_notification(self, info: Info, id: UUID) -> bool:
        """Delete a notification."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.delete_notification(id)

    # Settings
    @strawberry.mutation
    async def update_settings(self, info: Info, input: UpdateSettingsInput) -> UserSettings:
        """Update user settings."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.update_settings(input)

    # AI Planner
    @strawberry.mutation
    async def propose_events(
        self,
        info: Info,
        conversation_id: UUID,
        proposal: AIEventProposalInput,
    ) -> List[ProposedEvent]:
        """Propose events from AI planner."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.propose_events(conversation_id, proposal)

    @strawberry.mutation
    async def confirm_proposed_events(
        self,
        info: Info,
        conversation_id: UUID,
        event_ids: List[UUID],
    ) -> List[Event]:
        """Confirm proposed events."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.confirm_proposed_events(conversation_id, event_ids)

    @strawberry.mutation
    async def reject_proposed_events(
        self,
        info: Info,
        conversation_id: UUID,
        event_ids: List[UUID],
    ) -> bool:
        """Reject proposed events."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        return await user.reject_proposed_events(conversation_id, event_ids)


@strawberry.type
class Subscription:
    """GraphQL subscriptions for real-time updates."""

    @strawberry.subscription
    async def event_created(self, info: Info, user_id: UUID) -> AsyncGenerator[Event, None]:
        """Subscribe to event creation."""
        # Implementation would use Redis pub/sub
        yield

    @strawberry.subscription
    async def event_updated(self, info: Info, user_id: UUID) -> AsyncGenerator[Event, None]:
        """Subscribe to event updates."""
        yield

    @strawberry.subscription
    async def event_deleted(self, info: Info, user_id: UUID) -> AsyncGenerator[UUID, None]:
        """Subscribe to event deletions."""
        yield

    @strawberry.subscription
    async def notification_created(self, info: Info, user_id: UUID) -> AsyncGenerator[Notification, None]:
        """Subscribe to new notifications."""
        yield

    @strawberry.subscription
    async def message_received(self, info: Info, conversation_id: UUID) -> AsyncGenerator[Message, None]:
        """Subscribe to new messages in a conversation."""
        yield

    @strawberry.subscription
    async def reminder_triggered(self, info: Info, user_id: UUID) -> AsyncGenerator[EventReminder, None]:
        """Subscribe to triggered reminders."""
        yield


# Create schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)