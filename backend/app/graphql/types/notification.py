"""GraphQL Notification types."""
import strawberry
from typing import Optional, List
from datetime import datetime
import uuid
from app.graphql.types.scalars import DateTime, UUID
from app.graphql.types.enums import NotificationCategory
from app.graphql.types.event import PageInfo


@strawberry.type
class Notification:
    """Notification GraphQL type."""
    id: UUID
    user_id: UUID
    type: NotificationCategory
    title: str
    body: Optional[str]
    reference_id: Optional[UUID]
    reference_type: Optional[str]
    is_read: bool
    read_at: Optional[DateTime]
    created_at: DateTime


@strawberry.type
class NotificationEdge:
    """Notification edge for pagination."""
    node: Notification
    cursor: str


@strawberry.type
class NotificationConnection:
    """Notification connection for pagination."""
    edges: List[NotificationEdge]
    page_info: PageInfo
    total_count: int
    unread_count: int