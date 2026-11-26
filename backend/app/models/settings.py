"""UserSettings model."""
import uuid
from datetime import datetime
from typing import List
from sqlalchemy import String, DateTime, ForeignKey, func, ARRAY, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
import enum


class Theme(str, enum.Enum):
    """Theme enumeration."""
    LIGHT = "LIGHT"
    DARK = "DARK"
    SYSTEM = "SYSTEM"


class CalendarView(str, enum.Enum):
    """Calendar default view enumeration."""
    MONTH = "MONTH"
    WEEK = "WEEK"
    DAY = "DAY"
    YEAR = "YEAR"
    UPCOMING = "UPCOMING"
    PAST = "PAST"


class UserSettings(Base):
    """User settings model."""
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    theme: Mapped[Theme] = mapped_column(
        nullable=False,
        default=Theme.SYSTEM,
    )
    calendar_default_view: Mapped[CalendarView] = mapped_column(
        nullable=False,
        default=CalendarView.MONTH,
    )
    week_start_day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,  # 0=Sunday, 1=Monday
    )
    default_reminder_minutes: Mapped[List[int]] = mapped_column(
        ARRAY(Integer),
        nullable=False,
        default=lambda: [1440, 60, 15],
    )
    notification_email: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    notification_push: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    ai_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="openai",
    )
    ai_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="gpt-4o",
    )
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
    )
    date_format: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="YYYY-MM-DD",
    )
    time_format: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="24h",
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

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="settings",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id}, theme={self.theme})>"