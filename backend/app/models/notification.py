"""Notification model."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, func, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
import enum


class NotificationCategory(str, enum.Enum):
    """Notification category enumeration."""
    REMINDER = "REMINDER"
    EVENT_CREATED = "EVENT_CREATED"
    EVENT_UPDATED = "EVENT_UPDATED"
    EVENT_DELETED = "EVENT_DELETED"
    AI_SUGGESTION = "AI_SUGGESTION"
    SYSTEM = "SYSTEM"


class Notification(Base):
    """Notification model for in-app notifications."""
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[NotificationCategory] = mapped_column(
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    body: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        nullable=True,
    )
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_notifications_user", "user_id"),
        Index("ix_notifications_unread", "user_id", "is_read", postgresql_where=is_read == False),
        Index("ix_notifications_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type})>"