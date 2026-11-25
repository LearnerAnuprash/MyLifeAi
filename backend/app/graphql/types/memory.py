"""GraphQL Memory types."""
import strawberry
from typing import Optional, List
from datetime import datetime
import uuid
from app.graphql.types.scalars import DateTime, UUID
from app.graphql.types.enums import MemoryType


@strawberry.type
class UserMemory:
    """User memory GraphQL type."""
    id: UUID
    user_id: UUID
    memory_type: MemoryType
    title: str
    content: str
    embedding: Optional[List[float]]
    source_conversation_id: Optional[UUID]
    confidence: float
    is_active: bool
    created_at: DateTime
    updated_at: DateTime


@strawberry.type
class MemoryEdge:
    """Memory edge for pagination."""
    node: UserMemory
    cursor: str


@strawberry.type
class MemoryConnection:
    """Memory connection for pagination."""
    edges: List[MemoryEdge]
    page_info: "PageInfo"
    total_count: int


from app.graphql.types.event import PageInfo