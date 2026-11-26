"""Memory service."""
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import UserMemory, MemoryType
from app.models.conversation import Conversation
from app.graphql.types.inputs import CreateMemoryInput, UpdateMemoryInput, MemorySearchInput, MemoryFilterInput
from app.graphql.types.memory import UserMemory as GQLUserMemory, MemoryConnection, MemoryEdge
from app.graphql.types.event import PageInfo
from app.graphql.serializers import memory_to_gql


class MemoryService:
    """Memory service for personal AI memory management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_memories(
        self,
        user_id: uuid.UUID,
        filter: Optional[MemoryFilterInput] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> MemoryConnection:
        """Get user's memories with pagination."""
        query = select(UserMemory).where(
            UserMemory.user_id == user_id,
            UserMemory.deleted_at.is_(None),
        ).order_by(UserMemory.created_at.desc())

        if filter:
            if filter.memory_types:
                query = query.where(UserMemory.memory_type.in_(filter.memory_types))
            if filter.is_active is not None:
                query = query.where(UserMemory.is_active == filter.is_active)

        if after:
            try:
                after_id = uuid.UUID(after)
                result = await self.db.execute(
                    select(UserMemory.created_at).where(UserMemory.id == after_id)
                )
                after_time = result.scalar_one_or_none()
                if after_time:
                    query = query.where(UserMemory.created_at < after_time)
            except ValueError:
                pass

        query = query.limit(first + 1)
        result = await self.db.execute(query)
        memories = result.scalars().all()

        has_next_page = len(memories) > first
        if has_next_page:
            memories = memories[:first]

        gql_memories = [memory_to_gql(m) for m in memories]

        edges = [
            MemoryEdge(node=memory, cursor=str(memory.id))
            for memory in gql_memories
        ]

        # Total count
        count_query = select(func.count(UserMemory.id)).where(
            UserMemory.user_id == user_id,
            UserMemory.deleted_at.is_(None),
        )
        if filter:
            if filter.memory_types:
                count_query = count_query.where(UserMemory.memory_type.in_(filter.memory_types))
            if filter.is_active is not None:
                count_query = count_query.where(UserMemory.is_active == filter.is_active)
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar() or 0

        page_info = PageInfo(
            has_next_page=has_next_page,
            has_previous_page=after is not None,
            start_cursor=str(edges[0].node.id) if edges else None,
            end_cursor=str(edges[-1].node.id) if edges else None,
        )

        return MemoryConnection(
            edges=edges,
            page_info=page_info,
            total_count=total_count,
        )

    async def get_memory(
        self,
        user_id: uuid.UUID,
        memory_id: uuid.UUID,
    ) -> Optional[GQLUserMemory]:
        """Get memory by ID."""
        result = await self.db.execute(
            select(UserMemory).where(
                UserMemory.id == memory_id,
                UserMemory.user_id == user_id,
                UserMemory.deleted_at.is_(None),
            )
        )
        memory = result.scalar_one_or_none()

        if not memory:
            return None

        return memory_to_gql(memory)

    async def search_memory(
        self,
        user_id: uuid.UUID,
        input: MemorySearchInput,
    ) -> List[GQLUserMemory]:
        """Semantic search for memories using pgvector."""
        # For now, do a simple text search
        # In production, this would use pgvector for semantic similarity
        query = select(UserMemory).where(
            UserMemory.user_id == user_id,
            UserMemory.deleted_at.is_(None),
            UserMemory.is_active == True,
        )

        # Simple text search on title and content
        search_term = f"%{input.query}%"
        query = query.where(
            UserMemory.title.ilike(search_term) |
            UserMemory.content.ilike(search_term)
        )

        if input.memory_types:
            query = query.where(UserMemory.memory_type.in_(input.memory_types))

        query = query.limit(input.limit or 10)

        result = await self.db.execute(query)
        memories = result.scalars().all()

        return [memory_to_gql(m) for m in memories]

    async def create_memory(
        self,
        user_id: uuid.UUID,
        input: CreateMemoryInput,
    ) -> GQLUserMemory:
        """Create a new memory entry."""
        # Verify conversation exists if provided
        if input.source_conversation_id:
            result = await self.db.execute(
                select(Conversation).where(
                    Conversation.id == input.source_conversation_id,
                    Conversation.user_id == user_id,
                )
            )
            if not result.scalar_one_or_none():
                raise ValueError("Source conversation not found")

        memory = UserMemory(
            user_id=user_id,
            memory_type=input.memory_type,
            title=input.title,
            content=input.content,
            source_conversation_id=input.source_conversation_id,
            confidence=input.confidence or 1.0,
        )

        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)

        return memory_to_gql(memory)

    async def update_memory(
        self,
        user_id: uuid.UUID,
        memory_id: uuid.UUID,
        input: UpdateMemoryInput,
    ) -> GQLUserMemory:
        """Update a memory entry."""
        result = await self.db.execute(
            select(UserMemory).where(
                UserMemory.id == memory_id,
                UserMemory.user_id == user_id,
                UserMemory.deleted_at.is_(None),
            )
        )
        memory = result.scalar_one_or_none()

        if not memory:
            raise ValueError("Memory not found")

        update_data = input.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(memory, field, value)

        await self.db.commit()
        await self.db.refresh(memory)

        return memory_to_gql(memory)

    async def delete_memory(
        self,
        user_id: uuid.UUID,
        memory_id: uuid.UUID,
    ) -> bool:
        """Delete a memory entry (soft delete)."""
        result = await self.db.execute(
            select(UserMemory).where(
                UserMemory.id == memory_id,
                UserMemory.user_id == user_id,
                UserMemory.deleted_at.is_(None),
            )
        )
        memory = result.scalar_one_or_none()

        if not memory:
            raise ValueError("Memory not found")

        memory.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True

    async def bulk_create_memories(
        self,
        user_id: uuid.UUID,
        inputs: List[CreateMemoryInput],
    ) -> List[GQLUserMemory]:
        """Create multiple memory entries."""
        memories = []
        for input in inputs:
            memory = await self.create_memory(user_id, input)
            memories.append(memory)
        return memories
