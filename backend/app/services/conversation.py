"""Conversation service."""
from typing import Optional
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import async_session_maker
from app.models.conversation import Conversation, ConversationRole, Message
from app.models.user import User
from app.graphql.types.inputs import CreateConversationInput, SendMessageInput
from app.graphql.types.conversation import (
    Conversation as GQLConversation,
    ConversationConnection,
    ConversationEdge,
)
from app.graphql.types.event import PageInfo
from app.graphql.types.payloads import SendMessagePayload
from app.graphql.serializers import conversation_to_gql, message_to_gql
from app.services.ai import AIService, get_planner_response


class ConversationService:
    """Conversation service for AI chat management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_conversations(
        self,
        user_id: uuid.UUID,
        first: int = 20,
        after: Optional[str] = None,
    ) -> ConversationConnection:
        """Get user's conversations with pagination."""
        query = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.updated_at.desc())
        )

        if after:
            try:
                after_id = uuid.UUID(after)
                result = await self.db.execute(
                    select(Conversation.updated_at).where(Conversation.id == after_id)
                )
                after_time = result.scalar_one_or_none()
                if after_time:
                    query = query.where(Conversation.updated_at < after_time)
            except ValueError:
                pass

        query = query.limit(first + 1)
        result = await self.db.execute(query)
        conversations = result.scalars().all()

        has_next_page = len(conversations) > first
        if has_next_page:
            conversations = conversations[:first]

        edges = [
            ConversationEdge(node=conversation_to_gql(conversation), cursor=str(conversation.id))
            for conversation in conversations
        ]

        count_result = await self.db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
        )
        total_count = count_result.scalar() or 0

        page_info = PageInfo(
            has_next_page=has_next_page,
            has_previous_page=after is not None,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        )

        return ConversationConnection(
            edges=edges,
            page_info=page_info,
            total_count=total_count,
        )

    async def get_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Optional[GQLConversation]:
        """Get conversation by ID."""
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .options(selectinload(Conversation.messages))
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        return conversation_to_gql(conversation)

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        input: CreateConversationInput,
    ) -> GQLConversation:
        """Create a new conversation."""
        conversation = Conversation(
            user_id=user_id,
            title=input.title,
            model_provider=input.model_provider or "openai",
            model_name=input.model_name or "gpt-4o",
            system_prompt=input.system_prompt,
        )

        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation_to_gql(conversation)

    async def update_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        title: Optional[str] = None,
    ) -> GQLConversation:
        """Update conversation title."""
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .options(selectinload(Conversation.messages))
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError("Conversation not found")

        if title is not None:
            conversation.title = title

        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation_to_gql(conversation)

    async def delete_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> bool:
        """Delete a conversation (soft delete)."""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError("Conversation not found")

        conversation.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True

    async def send_message(
        self,
        user_id: uuid.UUID,
        input: SendMessageInput,
    ) -> SendMessagePayload:
        """Send a message and get an AI response with tool calling."""
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.id == input.conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .options(selectinload(Conversation.messages))
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError("Conversation not found")

        user_message = Message(
            conversation_id=conversation.id,
            role=ConversationRole.USER,
            content=input.content,
            tool_calls=None,
            tool_call_id=None,
            message_metadata=None,
        )
        self.db.add(user_message)
        await self.db.commit()
        await self.db.refresh(user_message)

        messages = []
        if conversation.system_prompt:
            messages.append({"role": "system", "content": conversation.system_prompt})
        for msg in conversation.messages:
            messages.append({"role": msg.role.value, "content": msg.content or ""})
        messages.append({"role": "user", "content": input.content})

        timezone_result = await self.db.execute(
            select(User.timezone).where(User.id == user_id)
        )
        user_timezone = timezone_result.scalar_one_or_none() or "UTC"

        ai_response = await get_planner_response(
            user_message=input.content,
            conversation_history=messages[:-1],
            user_context={
                "conversation_id": str(conversation.id),
                "timezone": user_timezone,
                "model_provider": "mock",
                "model_name": "gpt-4o",
            },
            ai_service=AIService(),
            user_id=user_id,
            db_session_factory=async_session_maker,
        )

        assistant_message = Message(
            conversation_id=conversation.id,
            role=ConversationRole.ASSISTANT,
            content=ai_response,
            tool_calls=None,
            tool_call_id=None,
            message_metadata=None,
        )
        self.db.add(assistant_message)

        conversation.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(assistant_message)

        return SendMessagePayload(
            user_message=message_to_gql(user_message),
            assistant_message=message_to_gql(assistant_message),
        )

