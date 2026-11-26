"""Reminder Celery tasks."""
from datetime import datetime, timezone
import uuid
from celery import shared_task
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.workers.utils import logger, run_async
from app.models.event import Event, EventReminder
from app.models.notification import NotificationCategory
from app.services.notification import NotificationService


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_due_reminders(self) -> dict:
    """Check for and send due reminders."""
    return run_async(_check_due_reminders())


async def _check_due_reminders() -> dict:
    """Async implementation of reminder checking."""
    sent_count = 0
    error_count = 0

    async with async_session_maker() as db:
        try:
            now = datetime.now(timezone.utc)

            # Find unsent reminders that are due
            # Reminder triggers at: event.start_time - minutes_before
            # So we need: now >= event.start_time - minutes_before
            # Which is: event.start_time <= now + minutes_before
            # Using raw SQL to calculate the interval
            result = await db.execute(
                select(EventReminder)
                .join(Event, EventReminder.event_id == Event.id)
                .where(
                    EventReminder.is_sent == False,
                    Event.deleted_at.is_(None),
                    Event.status == 'scheduled',
                    text("events.start_time <= now() + (event_reminders.minutes_before || ' minutes')::interval"),
                )
            )
            reminders = result.scalars().all()

            logger.info("found_due_reminders", count=len(reminders), now=now.isoformat())

            for reminder in reminders:
                logger.info(
                    "processing_reminder",
                    reminder_id=str(reminder.id),
                    event_id=str(reminder.event_id),
                )
                try:
                    # Send reminder notification
                    await _send_reminder_notification(db, reminder)

                    # Mark as sent
                    reminder.is_sent = True
                    reminder.sent_at = now

                    sent_count += 1
                    logger.info("sent_reminder", reminder_id=str(reminder.id))
                except Exception as e:
                    error_count += 1
                    # Log error but continue with other reminders
                    logger.error("send_reminder_failed", reminder_id=str(reminder.id), error=str(e))

            await db.commit()

        except Exception as e:
            await db.rollback()
            raise

    return {"sent": sent_count, "errors": error_count}


async def _send_reminder_notification(db: AsyncSession, reminder: EventReminder) -> None:
    """Send a reminder notification."""
    event = reminder.event

    # Create in-app notification
    notification_service = NotificationService(db)

    # Format time until event
    now = datetime.now(timezone.utc)
    time_until = event.start_time - now
    hours = int(time_until.total_seconds() // 3600)
    minutes = int((time_until.total_seconds() % 3600) // 60)

    if hours > 0:
        time_str = f"{hours}h {minutes}m"
    else:
        time_str = f"{minutes}m"

    title = f"Reminder: {event.title}"
    body = f"Starting in {time_str}"
    if event.location:
        body += f" at {event.location}"

    await notification_service.create_notification(
        user_id=reminder.user_id,
        type=NotificationCategory.REMINDER,
        title=title,
        body=body,
        reference_id=event.id,
        reference_type="event",
    )

    # TODO: Add email/push notification support based on reminder.notification_type


@shared_task(bind=True, max_retries=3)
def send_event_reminder(self, reminder_id: str) -> dict:
    """Send a specific reminder (for testing/manual triggering)."""
    return run_async(_send_event_reminder(reminder_id))


async def _send_event_reminder(reminder_id: str) -> dict:
    """Async implementation of sending specific reminder."""
    async with async_session_maker() as db:
        try:
            result = await db.execute(
                select(EventReminder).where(EventReminder.id == uuid.UUID(reminder_id))
            )
            reminder = result.scalar_one_or_none()

            if not reminder:
                return {"error": "Reminder not found"}

            if reminder.is_sent:
                return {"error": "Reminder already sent"}

            await _send_reminder_notification(db, reminder)

            reminder.is_sent = True
            reminder.sent_at = datetime.now(timezone.utc)

            await db.commit()

            return {"success": True, "reminder_id": reminder_id}

        except Exception as e:
            await db.rollback()
            return {"error": str(e)}


@shared_task
def schedule_event_reminders(event_id: str) -> dict:
    """Schedule reminders for a new/updated event."""
    return run_async(_schedule_event_reminders(event_id))


async def _schedule_event_reminders(event_id: str) -> dict:
    """Async implementation of scheduling event reminders."""
    async with async_session_maker() as db:
        try:
            result = await db.execute(
                select(Event).where(Event.id == uuid.UUID(event_id))
            )
            event = result.scalar_one_or_none()

            if not event:
                return {"error": "Event not found"}

            if event.is_recurring:
                # For recurring events, we schedule reminders for the next few instances
                # This is a simplified approach - in production, you'd use a more sophisticated scheduler
                return {"message": "Recurring event reminders scheduled via periodic task"}

            # For non-recurring events, reminders are created at event creation
            # and picked up by the periodic check_due_reminders task

            return {"success": True, "event_id": event_id}

        except Exception as e:
            return {"error": str(e)}
