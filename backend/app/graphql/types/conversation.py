"""GraphQL Conversation types."""
import strawberry
from typing import Optional, List
from datetime import datetime
import uuid
from app.graphql.types.scalars import DateTime, UUID, JSON
from app.graphql.types.enums import ConversationRole


@strawberry.type
class Message:
    """Message GraphQL type."""
    id: UUID
    conversation_id: UUID
    role: ConversationRole
    content: str
    tool_calls: Optional[JSON]
    tool_call_id: Optional[str]
    message_metadata: Optional[JSON]
    created_at: DateTime


@strawberry.type
class Conversation:
    """Conversation GraphQL type."""
    id: UUID
    user_id: UUID
    title: Optional[str]
    model_provider: str
    model_name: str
    system_prompt: Optional[str]
    messages: List[Message]
    created_at: DateTime
    updated_at: DateTime


@strawberry.type
class ConversationEdge:
    """Conversation edge for pagination."""
    node: Conversation
    cursor: str


@strawberry.type
class ConversationConnection:
    """Conversation connection for pagination."""
    edges: List[ConversationEdge]
    page_info: "PageInfo"
    total_count: int


# Need to import PageInfo
from app.graphql.types.event import PageInfo