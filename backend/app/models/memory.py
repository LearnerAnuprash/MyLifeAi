"""UserMemory model for personal AI memory."""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, ForeignKey, func, Index, Float, Boolean, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
import enum


class MemoryType(str, enum.Enum):
    """Memory type enumeration."""
    GOAL = "GOAL"
    PREFERENCE = "PREFERENCE"
    COMMITMENT = "COMMITMENT"
    FACT = "FACT"
    SUMMARY = "SUMMARY"


class UserMemory(Base):
    """User memory model for personal AI context."""
    __tablename__ = "user_memory"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_type: Mapped[MemoryType] = mapped_column(
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        ARRAY(Float),
        nullable=True,
    )
    source_conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="memories",
        lazy="selectin",
    )
    source_conversation: Mapped[Optional["Conversation"]] = relationship(
        "Conversation",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_memory_user", "user_id"),
        Index("ix_memory_type", "memory_type"),
        Index("ix_memory_active", "is_active", postgresql_where=is_active == True),
    )

    def __repr__(self) -> str:
        return f"<UserMemory(id={self.id}, type={self.memory_type}, title={self.title})>"