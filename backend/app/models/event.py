"""Event and EventReminder models."""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, ForeignKey,
    func, Index, ARRAY, Enum as SQLEnum, text
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
import enum


class EventStatus(str, enum.Enum):
    """Event status enumeration."""
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class EventPriority(str, enum.Enum):
    """Event priority enumeration."""
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationType(str, enum.Enum):
    """Notification type enumeration."""
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    PUSH = "PUSH"


class Event(Base):
    """Event model."""
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    all_day: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC",
    )
    priority: Mapped[EventPriority] = mapped_column(
        SQLEnum(EventPriority),
        nullable=False,
        default=EventPriority.NORMAL,
    )
    status: Mapped[EventStatus] = mapped_column(
        SQLEnum(EventStatus),
        nullable=False,
        default=EventStatus.SCHEDULED,
    )
    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    rrule: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    rrule_original_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    recurrence_exceptions: Mapped[List[datetime]] = mapped_column(
        ARRAY(DateTime(timezone=True)),
        nullable=False,
        server_default=text("'{}'::timestamptz[]"),
    )
    preparation_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
        back_populates="events",
        lazy="selectin",
    )
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="events",
        lazy="selectin",
    )
    reminders: Mapped[List["EventReminder"]] = relationship(
        "EventReminder",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_events_user", "user_id"),
        Index("ix_events_category", "category_id"),
        Index("ix_events_start_time", "start_time"),
        Index("ix_events_date_range", "user_id", "start_time", "end_time"),
        Index("ix_events_recurring", "is_recurring", postgresql_where=is_recurring == True),
        Index("ix_events_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title={self.title}, start={self.start_time})>"


class EventReminder(Base):
    """Event reminder model."""
    __tablename__ = "event_reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    minutes_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType),
        nullable=False,
        default=NotificationType.IN_APP,
    )
    is_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="reminders",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="event_reminders",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_reminders_event", "event_id"),
        Index(
            "ix_reminders_user_pending",
            "user_id",
            "is_sent",
            postgresql_where=is_sent == False,
        ),
        Index(
            "ix_reminders_scheduled",
            "minutes_before",
            postgresql_where=is_sent == False,
        ),
    )

    def __repr__(self) -> str:
        return f"<EventReminder(id={self.id}, event_id={self.event_id}, minutes_before={self.minutes_before})>"