"""User model (persistence only)."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.conversation import Conversation
    from app.models.event import Event, EventReminder
    from app.models.memory import UserMemory
    from app.models.notification import Notification
    from app.models.settings import UserSettings


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    categories: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    events: Mapped[list["Event"]] = relationship(
        "Event",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    memories: Mapped[list["UserMemory"]] = relationship(
        "UserMemory",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    settings: Mapped[Optional["UserSettings"]] = relationship(
        "UserSettings",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
    )
    event_reminders: Mapped[list["EventReminder"]] = relationship(
        "EventReminder",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_users_active", "is_active", postgresql_where=is_active == True),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
