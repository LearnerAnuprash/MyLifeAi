"""GraphQL payload types."""
import strawberry
from typing import Optional, List, Union
from datetime import datetime
import uuid
from app.graphql.types.scalars import DateTime, UUID
from app.graphql.types.enums import EventPriority
from app.graphql.types.category import Category
from app.graphql.types.event import EventReminder


@strawberry.type
class AuthPayload:
    """Authentication payload."""
    token: str
    refresh_token: str
    user: "User"


@strawberry.type
class SendMessagePayload:
    """Send message payload."""
    user_message: "Message"
    assistant_message: "Message"


@strawberry.type
class ProposedEvent:
    """Proposed event from AI planner."""
    id: UUID
    title: str
    description: Optional[str]
    suggested_start_time: DateTime
    suggested_end_time: DateTime
    category: Optional[Category]
    priority: EventPriority
    preparation_notes: Optional[str]
    reminders: List[EventReminder]


# Error types
@strawberry.type
class Success:
    success: bool = True


@strawberry.interface
class Error:
    message: str
    code: str


@strawberry.type
class ValidationError:
    message: str
    code: str
    field: str
    value: Optional[str] = None


@strawberry.type
class AuthenticationError:
    message: str
    code: str


@strawberry.type
class AuthorizationError:
    message: str
    code: str


@strawberry.type
class NotFoundError:
    message: str
    code: str
    resource: str
    id: UUID


MutationResult = Union[
    Success,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
]

# Forward references
from app.graphql.types.user import User
from app.graphql.types.conversation import Message