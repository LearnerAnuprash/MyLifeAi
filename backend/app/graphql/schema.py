"""GraphQL schema definition.

Resolvers are intentionally thin: authenticate, obtain the request-scoped
session, and delegate to a domain service. No SQL or model->GraphQL conversion
belongs in this module.
"""
from typing import AsyncGenerator, List, Optional

import strawberry
from graphql import GraphQLError
from strawberry.types import Info

from app.graphql.types import (
    # Types
    AIEventProposalInput,
    AuthPayload,
    BulkUpdateEventInput,
    CalendarRangeInput,
    Category,
    CategoryTree,
    Conversation,
    ConversationConnection,
    CreateCategoryInput,
    CreateConversationInput,
    CreateEventInput,
    CreateMemoryInput,
    Event,
    EventConnection,
    EventFilterInput,
    EventReminder,
    LoginInput,
    MemoryConnection,
    MemoryFilterInput,
    MemorySearchInput,
    Message,
    Notification,
    NotificationConnection,
    NotificationFilterInput,
    ProposedEvent,
    RegisterInput,
    SendMessageInput,
    SendMessagePayload,
    UpdateCategoryInput,
    UpdateEventInput,
    UpdateMemoryInput,
    UpdateSettingsInput,
    User,
    UserMemory,
    UserSettings,
)
from app.graphql.serializers import user_to_gql
from app.graphql.types.scalars import DateTime, UUID
from app.services.category import CategoryService
from app.services.conversation import ConversationService
from app.services.event import EventService
from app.services.memory import MemoryService
from app.services.notification import NotificationService
from app.services.settings import SettingsService


def require_user(info: Info):
    """Return the authenticated user or raise a GraphQL auth error."""
    user = info.context.get("user")
    if not user:
        raise GraphQLError("Authentication required")
    return user


@strawberry.type
class Query:
    """GraphQL queries."""

    @strawberry.field
    async def me(self, info: Info) -> Optional[User]:
        """Get current authenticated user."""
        user = info.context.get("user")
        if not user:
            return None
        return user_to_gql(user)

    @strawberry.field
    async def categories(self, info: Info) -> CategoryTree:
        """Get user's category tree."""
        user = require_user(info)
        return await CategoryService(info.context["db"]).get_category_tree(user.id)

    @strawberry.field
    async def category(self, info: Info, id: UUID) -> Optional[Category]:
        """Get category by ID."""
        user = require_user(info)
        return await CategoryService(info.context["db"]).get_category(user.id, id)

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
        user = require_user(info)
        return await EventService(info.context["db"]).get_events(
            user.id, filter, first, after, last, before
        )

    @strawberry.field
    async def event(self, info: Info, id: UUID) -> Optional[Event]:
        """Get event by ID."""
        user = require_user(info)
        return await EventService(info.context["db"]).get_event(user.id, id)

    @strawberry.field
    async def upcoming_events(
        self,
        info: Info,
        limit: int = 10,
        days: int = 30,
    ) -> List[Event]:
        """Get upcoming events."""
        user = require_user(info)
        return await EventService(info.context["db"]).get_upcoming_events(
            user.id, limit, days
        )

    @strawberry.field
    async def past_events(
        self,
        info: Info,
        limit: int = 10,
        days: int = 30,
    ) -> List[Event]:
        """Get past events."""
        user = require_user(info)
        return await EventService(info.context["db"]).get_past_events(user.id, limit, days)

    @strawberry.field
    async def events_by_date_range(
        self,
        info: Info,
        range: CalendarRangeInput,
    ) -> List[Event]:
        """Get events within a date range for calendar views."""
        user = require_user(info)
        return await EventService(info.context["db"]).get_events_by_date_range(
            user.id, range.start_date, range.end_date, range.timezone
        )

    @strawberry.field
    async def recurring_event_instances(
        self,
        info: Info,
        event_id: UUID,
        range: CalendarRangeInput,
    ) -> List[Event]:
        """Get recurring event instances within a range."""
        user = require_user(info)
        return await EventService(info.context["db"]).get_recurring_instances(
            user.id, event_id, range.start_date, range.end_date, range.timezone
        )

    @strawberry.field
    async def conversations(
        self,
        info: Info,
        first: int = 20,
        after: Optional[str] = None,
    ) -> ConversationConnection:
        """Get user's conversations."""
        user = require_user(info)
        return await ConversationService(info.context["db"]).get_conversations(
            user.id, first, after
        )

    @strawberry.field
    async def conversation(self, info: Info, id: UUID) -> Optional[Conversation]:
        """Get conversation by ID."""
        user = require_user(info)
        return await ConversationService(info.context["db"]).get_conversation(user.id, id)

    @strawberry.field
    async def memories(
        self,
        info: Info,
        filter: Optional[MemoryFilterInput] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> MemoryConnection:
        """Get user's memories."""
        user = require_user(info)
        return await MemoryService(info.context["db"]).get_memories(
            user.id, filter, first, after
        )

    @strawberry.field
    async def memory(self, info: Info, id: UUID) -> Optional[UserMemory]:
        """Get memory by ID."""
        user = require_user(info)
        return await MemoryService(info.context["db"]).get_memory(user.id, id)

    @strawberry.field
    async def search_memory(
        self,
        info: Info,
        input: MemorySearchInput,
    ) -> List[UserMemory]:
        """Search memories."""
        user = require_user(info)
        return await MemoryService(info.context["db"]).search_memory(user.id, input)

    @strawberry.field
    async def notifications(
        self,
        info: Info,
        filter: Optional[NotificationFilterInput] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> NotificationConnection:
        """Get user's notifications."""
        user = require_user(info)
        return await NotificationService(info.context["db"]).get_notifications(
            user.id, filter, first, after
        )

    @strawberry.field
    async def unread_notification_count(self, info: Info) -> int:
        """Get count of unread notifications."""
        user = require_user(info)
        return await NotificationService(info.context["db"]).get_unread_count(user.id)

    @strawberry.field
    async def calendar_events(
        self,
        info: Info,
        range: CalendarRangeInput,
    ) -> List[Event]:
        """Get events for calendar view."""
        user = require_user(info)
        return await EventService(info.context["db"]).get_calendar_events(
            user.id, range.start_date, range.end_date
        )

    @strawberry.field
    async def today_events(self, info: Info) -> List[Event]:
        """Get today's events."""
        user = require_user(info)
        return await EventService(info.context["db"]).get_today_events(user.id)

    @strawberry.field
    async def this_week_events(self, info: Info) -> List[Event]:
        """Get this week's events."""
        user = require_user(info)
        return await EventService(info.context["db"]).get_this_week_events(user.id)

    @strawberry.field
    async def this_month_events(self, info: Info) -> List[Event]:
        """Get this month's events."""
        user = require_user(info)
        return await EventService(info.context["db"]).get_this_month_events(user.id)


@strawberry.type
class Mutation:
    """GraphQL mutations."""

    # Auth
    @strawberry.mutation
    async def register(self, info: Info, input: RegisterInput) -> AuthPayload:
        """Register a new user."""
        from app.services.auth import AuthService

        return await AuthService(info.context["db"]).register(input)

    @strawberry.mutation
    async def login(self, info: Info, input: LoginInput) -> AuthPayload:
        """Login user."""
        from app.services.auth import AuthService

        return await AuthService(info.context["db"]).login(input)

    @strawberry.mutation
    async def logout(self, info: Info) -> bool:
        """Logout user (token invalidation handled client-side)."""
        return True

    @strawberry.mutation
    async def refresh_token(self, info: Info) -> str:
        """Refresh access token from the X-Refresh-Token header."""
        from app.services.auth import AuthService

        return await AuthService(info.context["db"]).refresh_token(
            info.context.get("refresh_token")
        )

    @strawberry.mutation
    async def verify_email(self, info: Info, token: str) -> bool:
        """Verify email address."""
        from app.services.auth import AuthService

        return await AuthService(info.context["db"]).verify_email(token)

    @strawberry.mutation
    async def request_password_reset(self, info: Info, email: str) -> bool:
        """Request password reset."""
        from app.services.auth import AuthService

        return await AuthService(info.context["db"]).request_password_reset(email)

    @strawberry.mutation
    async def reset_password(self, info: Info, token: str, password: str) -> bool:
        """Reset password with token."""
        from app.services.auth import AuthService

        return await AuthService(info.context["db"]).reset_password(token, password)

    # Categories
    @strawberry.mutation
    async def create_category(self, info: Info, input: CreateCategoryInput) -> Category:
        """Create a new category."""
        user = require_user(info)
        return await CategoryService(info.context["db"]).create_category(user.id, input)

    @strawberry.mutation
    async def update_category(
        self, info: Info, id: UUID, input: UpdateCategoryInput
    ) -> Category:
        """Update a category."""
        user = require_user(info)
        return await CategoryService(info.context["db"]).update_category(
            user.id, id, input
        )

    @strawberry.mutation
    async def delete_category(self, info: Info, id: UUID) -> bool:
        """Delete a category."""
        user = require_user(info)
        return await CategoryService(info.context["db"]).delete_category(user.id, id)

    @strawberry.mutation
    async def reorder_categories(
        self, info: Info, category_ids: List[UUID]
    ) -> List[Category]:
        """Reorder categories."""
        user = require_user(info)
        return await CategoryService(info.context["db"]).reorder_categories(
            user.id, category_ids
        )

    # Events
    @strawberry.mutation
    async def create_event(self, info: Info, input: CreateEventInput) -> Event:
        """Create a new event."""
        user = require_user(info)
        return await EventService(info.context["db"]).create_event(user.id, input)

    @strawberry.mutation
    async def update_event(self, info: Info, id: UUID, input: UpdateEventInput) -> Event:
        """Update an event."""
        user = require_user(info)
        return await EventService(info.context["db"]).update_event(user.id, id, input)

    @strawberry.mutation
    async def delete_event(self, info: Info, id: UUID) -> bool:
        """Delete an event."""
        user = require_user(info)
        return await EventService(info.context["db"]).delete_event(user.id, id)

    @strawberry.mutation
    async def duplicate_event(self, info: Info, id: UUID, new_start_time: DateTime) -> Event:
        """Duplicate an event to a new date."""
        user = require_user(info)
        return await EventService(info.context["db"]).duplicate_event(
            user.id, id, new_start_time
        )

    @strawberry.mutation
    async def complete_event(self, info: Info, id: UUID) -> Event:
        """Mark event as completed."""
        user = require_user(info)
        return await EventService(info.context["db"]).complete_event(user.id, id)

    @strawberry.mutation
    async def bulk_create_events(
        self, info: Info, inputs: List[CreateEventInput]
    ) -> List[Event]:
        """Create multiple events."""
        user = require_user(info)
        return await EventService(info.context["db"]).bulk_create_events(user.id, inputs)

    @strawberry.mutation
    async def bulk_update_events(
        self, info: Info, inputs: List[BulkUpdateEventInput]
    ) -> List[Event]:
        """Update multiple events."""
        user = require_user(info)
        return await EventService(info.context["db"]).bulk_update_events(user.id, inputs)

    @strawberry.mutation
    async def bulk_delete_events(self, info: Info, ids: List[UUID]) -> bool:
        """Delete multiple events."""
        user = require_user(info)
        return await EventService(info.context["db"]).bulk_delete_events(user.id, ids)

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
        user = require_user(info)
        return await EventService(info.context["db"]).create_recurring_exception(
            user.id, event_id, exception_date, input
        )

    @strawberry.mutation
    async def update_recurring_series(
        self,
        info: Info,
        event_id: UUID,
        input: UpdateEventInput,
    ) -> Event:
        """Update entire recurring series."""
        user = require_user(info)
        return await EventService(info.context["db"]).update_recurring_series(
            user.id, event_id, input
        )

    @strawberry.mutation
    async def delete_recurring_series(
        self,
        info: Info,
        event_id: UUID,
        delete_future: bool = True,
    ) -> bool:
        """Delete recurring series."""
        user = require_user(info)
        return await EventService(info.context["db"]).delete_recurring_series(
            user.id, event_id, delete_future
        )

    # Conversations
    @strawberry.mutation
    async def create_conversation(
        self, info: Info, input: CreateConversationInput
    ) -> Conversation:
        """Create a new conversation."""
        user = require_user(info)
        return await ConversationService(info.context["db"]).create_conversation(
            user.id, input
        )

    @strawberry.mutation
    async def update_conversation(
        self, info: Info, id: UUID, title: Optional[str] = None
    ) -> Conversation:
        """Update conversation title."""
        user = require_user(info)
        return await ConversationService(info.context["db"]).update_conversation(
            user.id, id, title
        )

    @strawberry.mutation
    async def delete_conversation(self, info: Info, id: UUID) -> bool:
        """Delete a conversation."""
        user = require_user(info)
        return await ConversationService(info.context["db"]).delete_conversation(
            user.id, id
        )

    @strawberry.mutation
    async def send_message(self, info: Info, input: SendMessageInput) -> SendMessagePayload:
        """Send a message and get AI response."""
        user = require_user(info)
        return await ConversationService(info.context["db"]).send_message(user.id, input)

    # Memory
    @strawberry.mutation
    async def create_memory(self, info: Info, input: CreateMemoryInput) -> UserMemory:
        """Create a memory entry."""
        user = require_user(info)
        return await MemoryService(info.context["db"]).create_memory(user.id, input)

    @strawberry.mutation
    async def update_memory(
        self, info: Info, id: UUID, input: UpdateMemoryInput
    ) -> UserMemory:
        """Update a memory entry."""
        user = require_user(info)
        return await MemoryService(info.context["db"]).update_memory(user.id, id, input)

    @strawberry.mutation
    async def delete_memory(self, info: Info, id: UUID) -> bool:
        """Delete a memory entry."""
        user = require_user(info)
        return await MemoryService(info.context["db"]).delete_memory(user.id, id)

    @strawberry.mutation
    async def bulk_create_memories(
        self, info: Info, inputs: List[CreateMemoryInput]
    ) -> List[UserMemory]:
        """Create multiple memory entries."""
        user = require_user(info)
        return await MemoryService(info.context["db"]).bulk_create_memories(
            user.id, inputs
        )

    # Notifications
    @strawberry.mutation
    async def mark_notification_read(self, info: Info, id: UUID) -> Notification:
        """Mark notification as read."""
        user = require_user(info)
        return await NotificationService(info.context["db"]).mark_read(user.id, id)

    @strawberry.mutation
    async def mark_all_notifications_read(self, info: Info) -> bool:
        """Mark all notifications as read."""
        user = require_user(info)
        return await NotificationService(info.context["db"]).mark_all_read(user.id)

    @strawberry.mutation
    async def delete_notification(self, info: Info, id: UUID) -> bool:
        """Delete a notification."""
        user = require_user(info)
        return await NotificationService(info.context["db"]).delete_notification(
            user.id, id
        )

    # Settings
    @strawberry.mutation
    async def update_settings(
        self, info: Info, input: UpdateSettingsInput
    ) -> UserSettings:
        """Update user settings."""
        user = require_user(info)
        return await SettingsService(info.context["db"]).update_settings(user.id, input)

    # AI Planner
    @strawberry.mutation
    async def propose_events(
        self,
        info: Info,
        conversation_id: UUID,
        proposal: AIEventProposalInput,
    ) -> List[ProposedEvent]:
        """Propose events from AI planner."""
        user = require_user(info)
        return await EventService(info.context["db"]).propose_events(
            user.id, conversation_id, proposal
        )

    @strawberry.mutation
    async def confirm_proposed_events(
        self,
        info: Info,
        conversation_id: UUID,
        event_ids: List[UUID],
    ) -> List[Event]:
        """Confirm proposed events."""
        user = require_user(info)
        return await EventService(info.context["db"]).confirm_proposed_events(
            user.id, conversation_id, event_ids
        )

    @strawberry.mutation
    async def reject_proposed_events(
        self,
        info: Info,
        conversation_id: UUID,
        event_ids: List[UUID],
    ) -> bool:
        """Reject proposed events."""
        user = require_user(info)
        return await EventService(info.context["db"]).reject_proposed_events(
            user.id, conversation_id, event_ids
        )


@strawberry.type
class Subscription:
    """GraphQL subscriptions for real-time updates.

    All subscriptions are explicit stubs until Redis pub/sub wiring lands.
    """

    @strawberry.subscription
    async def event_created(
        self, info: Info, user_id: UUID
    ) -> AsyncGenerator[Optional[Event], None]:
        """Subscribe to event creation."""
        # TODO: implement with Redis pub/sub
        yield None

    @strawberry.subscription
    async def event_updated(
        self, info: Info, user_id: UUID
    ) -> AsyncGenerator[Optional[Event], None]:
        """Subscribe to event updates."""
        # TODO: implement with Redis pub/sub
        yield None

    @strawberry.subscription
    async def event_deleted(
        self, info: Info, user_id: UUID
    ) -> AsyncGenerator[Optional[UUID], None]:
        """Subscribe to event deletions."""
        # TODO: implement with Redis pub/sub
        yield None

    @strawberry.subscription
    async def notification_created(
        self, info: Info, user_id: UUID
    ) -> AsyncGenerator[Optional[Notification], None]:
        """Subscribe to new notifications."""
        # TODO: implement with Redis pub/sub
        yield None

    @strawberry.subscription
    async def message_received(
        self, info: Info, conversation_id: UUID
    ) -> AsyncGenerator[Optional[Message], None]:
        """Subscribe to new messages in a conversation."""
        # TODO: implement with Redis pub/sub
        yield None

    @strawberry.subscription
    async def reminder_triggered(
        self, info: Info, user_id: UUID
    ) -> AsyncGenerator[Optional[EventReminder], None]:
        """Subscribe to triggered reminders."""
        # TODO: implement with Redis pub/sub
        yield None


# Create schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)
