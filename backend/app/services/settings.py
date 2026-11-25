"""Settings service."""
from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import UserSettings, Theme, CalendarView
from app.graphql.types.inputs import UpdateSettingsInput
from app.graphql.types.user import UserSettings as GQLUserSettings


class SettingsService:
    """Settings service for user preferences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self, user_id: uuid.UUID) -> GQLUserSettings:
        """Get user settings."""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            # Create default settings
            settings = UserSettings(user_id=user_id)
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)

        return self._settings_to_gql(settings)

    async def update_settings(
        self,
        user_id: uuid.UUID,
        input: UpdateSettingsInput,
    ) -> GQLUserSettings:
        """Update user settings."""
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = UserSettings(user_id=user_id)
            self.db.add(settings)

        update_data = input.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(settings, field):
                setattr(settings, field, value)

        await self.db.commit()
        await self.db.refresh(settings)

        return self._settings_to_gql(settings)

    def _settings_to_gql(self, settings: UserSettings) -> GQLUserSettings:
        """Convert UserSettings model to GraphQL type."""
        return GQLUserSettings(
            theme=settings.theme,
            calendar_default_view=settings.calendar_default_view,
            week_start_day=settings.week_start_day,
            default_reminder_minutes=settings.default_reminder_minutes,
            notification_email=settings.notification_email,
            notification_push=settings.notification_push,
            ai_provider=settings.ai_provider,
            ai_model=settings.ai_model,
            language=settings.language,
            date_format=settings.date_format,
            time_format=settings.time_format,
        )