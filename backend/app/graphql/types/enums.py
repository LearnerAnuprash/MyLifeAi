"""GraphQL enums."""
import strawberry
from app.models.event import EventStatus, EventPriority, NotificationType
from app.models.conversation import ConversationRole
from app.models.memory import MemoryType
from app.models.notification import NotificationCategory
from app.models.settings import CalendarView, Theme


# Re-export enums as Strawberry enums
EventStatus = strawberry.enum(EventStatus)
EventPriority = strawberry.enum(EventPriority)
NotificationType = strawberry.enum(NotificationType)
ConversationRole = strawberry.enum(ConversationRole)
MemoryType = strawberry.enum(MemoryType)
NotificationCategory = strawberry.enum(NotificationCategory)
CalendarView = strawberry.enum(CalendarView)
Theme = strawberry.enum(Theme)