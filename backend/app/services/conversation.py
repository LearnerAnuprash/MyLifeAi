"""Conversation service."""
from typing import List, Optional
import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message, ConversationRole
from app.graphql.types.inputs import CreateConversationInput, SendMessageInput
from app.graphql.types.conversation import Conversation as GQLConversation, Message as GQLMessage
from app.graphql.types.payloads import SendMessagePayload


class ConversationService:
    """Conversation service for AI chat management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_conversations(
        self,
        user_id: uuid.UUID,
        first: int = 20,
        after: Optional[str] = None,
    ) -> GQLConversation:
        """Get user's conversations with pagination."""
        query = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
        ).options(
            selectinload(Conversation.messages),
        ).order_by(Conversation.updated_at.desc())

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

        gql_conversations = [await self._conversation_to_gql(c) for c in conversations]

        # Need to return connection type - this is a simplified version
        return gql_conversations

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

        return await self._conversation_to_gql(conversation)

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

        return await self._conversation_to_gql(conversation)

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

        return await self._conversation_to_gql(conversation)

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

        conversation.deleted_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def send_message(
        self,
        user_id: uuid.UUID,
        input: SendMessageInput,
    ) -> SendMessagePayload:
        """Send a message and get AI response."""
        # Get conversation
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

        # Create user message
        user_message = Message(
            conversation_id=conversation.id,
            role=ConversationRole.USER,
            content=input.content,
            tool_calls=None,
            tool_call_id=None,
            metadata=None,
        )
        self.db.add(user_message)

        # TODO: Call AI service to get response
        # For now, create a placeholder assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role=ConversationRole.ASSISTANT,
            content="AI response placeholder - integrate with AIService",
            tool_calls=None,
            tool_call_id=None,
            metadata=None,
        )
        self.db.add(assistant_message)

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user_message)
        await self.db.refresh(assistant_message)

        return SendMessagePayload(
            user_message=await self._message_to_gql(user_message),
            assistant_message=await self._message_to_gql(assistant_message),
        )

    async def _conversation_to_gql(self, conversation: Conversation) -> GQLConversation:
        """Convert Conversation model to GraphQL type."""
        messages = []
        if conversation.messages:
            for msg in sorted(conversation.messages, key=lambda m: m.created_at):
                messages.append(await self._message_to_gql(msg))

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

    async def _message_to_gql(self, message: Message) -> GQLMessage:
        """Convert Message model to GraphQL type."""
        return GQLMessage(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            tool_calls=message.tool_calls,
            tool_call_id=message.tool_call_id,
            metadata=message.metadata,
            created_at=message.created_at,
        )