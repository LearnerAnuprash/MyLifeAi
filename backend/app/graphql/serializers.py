"""Single home for SQLAlchemy model -> GraphQL type conversion."""
from typing import Optional

from app.models.category import Category
from app.models.conversation import Conversation, Message
from app.models.event import Event, EventReminder
from app.models.memory import UserMemory
from app.models.notification import Notification
from app.models.settings import UserSettings
from app.models.user import User

from app.graphql.types.category import Category as GQLCategory
from app.graphql.types.conversation import Conversation as GQLConversation
from app.graphql.types.conversation import Message as GQLMessage
from app.graphql.types.event import Event as GQLEvent
from app.graphql.types.event import EventReminder as GQLEventReminder
from app.graphql.types.memory import UserMemory as GQLUserMemory
from app.graphql.types.notification import Notification as GQLNotification
from app.graphql.types.user import User as GQLUser
from app.graphql.types.user import UserSettings as GQLUserSettings


def category_to_gql(category: Category) -> GQLCategory:
    """Convert a Category model (with loaded children) to its GraphQL type."""
    children = [
        category_to_gql(child)
        for child in (category.children or [])
        if child.deleted_at is None
    ]

    return GQLCategory(
        id=category.id,
        user_id=category.user_id,
        parent_id=category.parent_id,
        name=category.name,
        description=category.description,
        color=category.color,
        icon=category.icon,
        is_system=category.is_system,
        sort_order=category.sort_order,
        default_reminder_minutes=category.default_reminder_minutes,
        children=children,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def reminder_to_gql(reminder: EventReminder) -> GQLEventReminder:
    """Convert an EventReminder model to its GraphQL type."""
    return GQLEventReminder(
        id=reminder.id,
        event_id=reminder.event_id,
        user_id=reminder.user_id,
        minutes_before=reminder.minutes_before,
        notification_type=reminder.notification_type,
        is_sent=reminder.is_sent,
        sent_at=reminder.sent_at,
        created_at=reminder.created_at,
    )


def event_to_gql(event: Event, reminders_override: list = None, category_override: dict = None) -> GQLEvent:
    """Convert an Event model to its GraphQL type."""
    if category_override is not None:
        category = category_from_dict(category_override)
    else:
        category = category_to_gql(event.category) if event.category else None

    if reminders_override is not None:
        # Handle both EventReminder objects and plain dicts
        reminders = []
        for reminder in reminders_override:
            if isinstance(reminder, dict):
                reminders.append(reminder_to_gql_from_dict(reminder))
            else:
                reminders.append(reminder_to_gql(reminder))
    else:
        reminders = [reminder_to_gql(reminder) for reminder in (event.reminders or [])]

    return GQLEvent(
        id=event.id,
        user_id=event.user_id,
        category=category,
        title=event.title,
        description=event.description,
        location=event.location,
        start_time=event.start_time,
        end_time=event.end_time,
        all_day=event.all_day,
        timezone=event.timezone,
        priority=event.priority,
        status=event.status,
        is_recurring=event.is_recurring,
        rrule=event.rrule,
        rrule_original_start=event.rrule_original_start,
        recurrence_exceptions=list(event.recurrence_exceptions or []),
        preparation_notes=event.preparation_notes,
        completed_at=event.completed_at,
        created_at=event.created_at,
        updated_at=event.updated_at,
        reminders=reminders,
    )


def category_from_dict(category: dict) -> GQLCategory:
    """Convert a category dict to its GraphQL type."""
    return GQLCategory(
        id=category["id"],
        user_id=category["user_id"],
        parent_id=category["parent_id"],
        name=category["name"],
        description=category["description"],
        color=category["color"],
        icon=category["icon"],
        is_system=category["is_system"],
        sort_order=category["sort_order"],
        default_reminder_minutes=category["default_reminder_minutes"],
        children=[],
        created_at=category["created_at"],
        updated_at=category["updated_at"],
    )


def reminder_to_gql_from_dict(reminder: dict) -> GQLEventReminder:
    """Convert a reminder dict to its GraphQL type."""
    return GQLEventReminder(
        id=reminder["id"],
        event_id=reminder["event_id"],
        user_id=reminder["user_id"],
        minutes_before=reminder["minutes_before"],
        notification_type=reminder["notification_type"],
        is_sent=reminder["is_sent"],
        sent_at=reminder["sent_at"],
        created_at=reminder["created_at"],
    )


def message_to_gql(message: Message) -> GQLMessage:
    """Convert a Message model to its GraphQL type."""
    return GQLMessage(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content or "",
        tool_calls=message.tool_calls,
        tool_call_id=message.tool_call_id,
        message_metadata=message.message_metadata,
        created_at=message.created_at,
    )


def conversation_to_gql(conversation: Conversation) -> GQLConversation:
    """Convert a Conversation model (with loaded messages) to its GraphQL type."""
    messages = [
        message_to_gql(message)
        for message in sorted(conversation.messages or [], key=lambda m: m.created_at)
    ]

    return GQLConversation(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        model_provider=conversation.model_provider,
        model_name=conversation.model_name,
        system_prompt=conversation.system_prompt,
        messages=messages,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def memory_to_gql(memory: UserMemory) -> GQLUserMemory:
    """Convert a UserMemory model to its GraphQL type."""
    return GQLUserMemory(
        id=memory.id,
        user_id=memory.user_id,
        memory_type=memory.memory_type,
        title=memory.title,
        content=memory.content,
        embedding=memory.embedding,
        source_conversation_id=memory.source_conversation_id,
        confidence=memory.confidence,
        is_active=memory.is_active,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )


def notification_to_gql(notification: Notification) -> GQLNotification:
    """Convert a Notification model to its GraphQL type."""
    return GQLNotification(
        id=notification.id,
        user_id=notification.user_id,
        type=notification.type,
        title=notification.title,
        body=notification.body,
        reference_id=notification.reference_id,
        reference_type=notification.reference_type,
        is_read=notification.is_read,
        read_at=notification.read_at,
        created_at=notification.created_at,
    )


def settings_to_gql(settings: UserSettings) -> GQLUserSettings:
    """Convert a UserSettings model to its GraphQL type."""
    return GQLUserSettings(
        theme=settings.theme,
        calendar_default_view=settings.calendar_default_view,
        week_start_day=settings.week_start_day,
        default_reminder_minutes=settings.default_reminder_minutes,
        notification_email=settings.notification_email,
        notification_push=settings.notification_push,
        ai_provider=settings.ai_provider,
        ai_model=settings.ai_model,
        language=settings.language,
        date_format=settings.date_format,
        time_format=settings.time_format,
    )


def user_to_gql(
    user: User,
    settings: Optional[UserSettings] = None,
) -> GQLUser:
    """Convert a User model to its GraphQL type.

    ``settings`` may be passed explicitly when the relationship is not loaded.
    """
    settings = settings if settings is not None else user.settings
    gql_settings = settings_to_gql(settings) if settings else GQLUserSettings(
        theme="system",
        calendar_default_view="month",
        week_start_day=0,
        default_reminder_minutes=[1440, 60, 15],
        notification_email=False,
        notification_push=False,
        ai_provider="openai",
        ai_model="gpt-4o",
        language="en",
        date_format="YYYY-MM-DD",
        time_format="24h",
    )

    return GQLUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        timezone=user.timezone,
        locale=user.locale,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
        settings=gql_settings,
    )
