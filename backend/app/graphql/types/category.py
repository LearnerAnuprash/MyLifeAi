"""GraphQL Category types."""
import strawberry
from typing import Optional, List
from datetime import datetime
import uuid
from app.graphql.types.scalars import DateTime, UUID


@strawberry.type
class Category:
    """Category GraphQL type."""
    id: UUID
    user_id: UUID
    parent_id: Optional[UUID]
    name: str
    description: Optional[str]
    color: str
    icon: Optional[str]
    is_system: bool
    sort_order: int
    default_reminder_minutes: List[int]
    children: List["Category"]
    created_at: DateTime
    updated_at: DateTime


@strawberry.type
class CategoryTree:
    """Category tree with flat list for easier client usage."""
    categories: List[Category]
    flat_list: List[Category]