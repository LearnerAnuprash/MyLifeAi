"""Notification Celery tasks."""
from datetime import datetime, timedelta, timezone
import uuid
from celery import shared_task
from sqlalchemy import select

from app.db.session import async_session_maker
from app.workers.utils import logger, run_async
from app.models.event import Event, EventStatus
from app.models.notification import Notification, NotificationCategory
from app.models.user import User
from app.models.settings import UserSettings
from app.services.notification import NotificationService


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_daily_summary(self) -> dict:
    """Send daily upcoming event summary to all users."""
    return run_async(_send_daily_summary())


async def _send_daily_summary() -> dict:
    """Async implementation of daily summary."""
    sent_count = 0
    error_count = 0

    async with async_session_maker() as db:
        try:
            now = datetime.now(timezone.utc)
            tomorrow = now + timedelta(days=1)
            week_from_now = now + timedelta(days=7)

            # Get all active users with email notifications enabled
            result = await db.execute(
                select(User)
                .join(User.settings)
                .where(
                    User.is_active == True,
                    User.deleted_at.is_(None),
                    UserSettings.notification_email == True,
                )
            )
            users = result.scalars().all()

            for user in users:
                try:
                    # Get upcoming events for today and tomorrow
                    events_result = await db.execute(
                        select(Event)
                        .where(
                            Event.user_id == user.id,
                            Event.deleted_at.is_(None),
                            Event.status == EventStatus.SCHEDULED,
                            Event.start_time >= now,
                            Event.start_time <= tomorrow,
                        )
                        .order_by(Event.start_time)
                    )
                    today_events = events_result.scalars().all()

                    # Get upcoming events for the week
                    week_result = await db.execute(
                        select(Event)
                        .where(
                            Event.user_id == user.id,
                            Event.deleted_at.is_(None),
                            Event.status == EventStatus.SCHEDULED,
                            Event.start_time > tomorrow,
                            Event.start_time <= week_from_now,
                        )
                        .order_by(Event.start_time)
                        .limit(10)
                    )
                    week_events = week_result.scalars().all()

                    if not today_events and not week_events:
                        continue  # No events, skip summary

                    # Create summary notification
                    notification_service = NotificationService(db)

                    today_count = len(today_events)
                    week_count = len(week_events)

                    title = "Your Daily Summary"
                    body_parts = []

                    if today_events:
                        body_parts.append(f"Today ({today_count} event{'s' if today_count != 1 else ''}):")
                        for event in today_events[:5]:
                            time_str = event.start_time.strftime("%I:%M %p")
                            body_parts.append(f"  • {time_str} - {event.title}")
                        if today_count > 5:
                            body_parts.append(f"  ... and {today_count - 5} more")

                    if week_events:
                        body_parts.append(f"\nThis Week ({week_count} upcoming):")
                        for event in week_events[:5]:
                            day_str = event.start_time.strftime("%a %m/%d")
                            time_str = event.start_time.strftime("%I:%M %p")
                            body_parts.append(f"  • {day_str} {time_str} - {event.title}")
                        if week_count > 5:
                            body_parts.append(f"  ... and {week_count - 5} more")

                    body = "\n".join(body_parts)

                    await notification_service.create_notification(
                        user_id=user.id,
                        type=NotificationCategory.SYSTEM,
                        title=title,
                        body=body,
                    )

                    # TODO: Send actual email via SMTP

                    sent_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error("daily_summary_failed", user_id=str(user.id), error=str(e))

            await db.commit()

        except Exception as e:
            await db.rollback()
            raise

    return {"sent": sent_count, "errors": error_count}


@shared_task(bind=True, max_retries=3)
def send_event_notification(self, user_id: str, notification_type: str, title: str, body: str, reference_id: str = None, reference_type: str = None) -> dict:
    """Send a notification to a specific user."""
    return run_async(_send_event_notification(user_id, notification_type, title, body, reference_id, reference_type))


async def _send_event_notification(
    user_id: str,
    notification_type: str,
    title: str,
    body: str,
    reference_id: str = None,
    reference_type: str = None
) -> dict:
    """Async implementation of sending event notification."""
    async with async_session_maker() as db:
        try:
            notification_service = NotificationService(db)

            await notification_service.create_notification(
                user_id=uuid.UUID(user_id),
                type=NotificationCategory(notification_type),
                title=title,
                body=body,
                reference_id=uuid.UUID(reference_id) if reference_id else None,
                reference_type=reference_type,
            )

            # TODO: Send email/push if user has them enabled

            return {"success": True}

        except Exception as e:
            return {"error": str(e)}


@shared_task
def send_weekly_summary() -> dict:
    """Send weekly summary (can be scheduled for weekends)."""
    return run_async(_send_weekly_summary())


async def _send_weekly_summary() -> dict:
    """Async implementation of weekly summary."""
    sent_count = 0
    error_count = 0

    async with async_session_maker() as db:
        try:
            now = datetime.now(timezone.utc)
            week_start = now - timedelta(days=now.weekday())
            week_end = week_start + timedelta(days=7)

            # Get users with weekly summary enabled
            result = await db.execute(
                select(User)
                .join(UserSettings)
                .where(
                    User.is_active == True,
                    User.deleted_at.is_(None),
                    UserSettings.notification_email == True,
                )
            )
            users = result.scalars().all()

            for user in users:
                try:
                    # Get completed events this week
                    completed_result = await db.execute(
                        select(Event)
                        .where(
                            Event.user_id == user.id,
                            Event.deleted_at.is_(None),
                            Event.status == EventStatus.COMPLETED,
                            Event.completed_at >= week_start,
                            Event.completed_at < week_end,
                        )
                        .order_by(Event.completed_at.desc())
                    )
                    completed_events = completed_result.scalars().all()

                    # Get upcoming events next week
                    next_week_end = week_end + timedelta(days=7)
                    upcoming_result = await db.execute(
                        select(Event)
                        .where(
                            Event.user_id == user.id,
                            Event.deleted_at.is_(None),
                            Event.status == EventStatus.SCHEDULED,
                            Event.start_time >= week_end,
                            Event.start_time < next_week_end,
                        )
                        .order_by(Event.start_time)
                        .limit(15)
                    )
                    upcoming_events = upcoming_result.scalars().all()

                    if not completed_events and not upcoming_events:
                        continue

                    notification_service = NotificationService(db)

                    title = "Your Weekly Summary"
                    body_parts = []

                    if completed_events:
                        body_parts.append(f"Completed this week ({len(completed_events)}):")
                        for event in completed_events[:10]:
                            day = event.completed_at.strftime("%a %m/%d")
                            body_parts.append(f"  ✓ {day} - {event.title}")

                    if upcoming_events:
                        body_parts.append(f"\nComing up next week ({len(upcoming_events)}):")
                        for event in upcoming_events[:10]:
                            day = event.start_time.strftime("%a %m/%d")
                            time_str = event.start_time.strftime("%I:%M %p")
                            body_parts.append(f"  • {day} {time_str} - {event.title}")

                    body = "\n".join(body_parts)

                    await notification_service.create_notification(
                        user_id=user.id,
                        type=NotificationCategory.SYSTEM,
                        title=title,
                        body=body,
                    )

                    sent_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error("weekly_summary_failed", user_id=str(user.id), error=str(e))

            await db.commit()

        except Exception as e:
            await db.rollback()
            raise

    return {"sent": sent_count, "errors": error_count}
