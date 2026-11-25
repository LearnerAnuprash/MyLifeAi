"""Maintenance Celery tasks."""
from datetime import datetime, timedelta
import asyncio
from celery import shared_task
from sqlalchemy import delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.event import EventReminder
from app.models.notification import Notification


def run_async(coro):
    """Run async function in new event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(bind=True, max_retries=3)
def cleanup_old_reminders(self, days_old: int = 90) -> dict:
    """Clean up old sent reminders."""
    return run_async(_cleanup_old_reminders(days_old))


async def _cleanup_old_reminders(days_old: int = 90) -> dict:
    """Async implementation of cleaning old reminders."""
    async with async_session_maker() as db:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Delete old sent reminders
            result = await db.execute(
                delete(EventReminder).where(
                    EventReminder.is_sent == True,
                    EventReminder.sent_at < cutoff_date,
                )
            )

            deleted_count = result.rowcount
            await db.commit()

            return {"deleted": deleted_count, "cutoff_date": cutoff_date.isoformat()}

        except Exception as e:
            await db.rollback()
            return {"error": str(e)}


@shared_task(bind=True, max_retries=3)
def cleanup_old_notifications(self, days_old: int = 180) -> dict:
    """Clean up old read notifications."""
    return run_async(_cleanup_old_notifications(days_old))


async def _cleanup_old_notifications(days_old: int = 180) -> dict:
    """Async implementation of cleaning old notifications."""
    async with async_session_maker() as db:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Delete old read notifications
            result = await db.execute(
                delete(Notification).where(
                    Notification.is_read == True,
                    Notification.read_at < cutoff_date,
                )
            )

            deleted_count = result.rowcount
            await db.commit()

            return {"deleted": deleted_count, "cutoff_date": cutoff_date.isoformat()}

        except Exception as e:
            await db.rollback()
            return {"error": str(e)}


@shared_task(bind=True, max_retries=3)
def cleanup_soft_deleted(self, days_old: int = 30) -> dict:
    """Permanently delete soft-deleted records older than threshold."""
    return run_async(_cleanup_soft_deleted(days_old))


async def _cleanup_soft_deleted(days_old: int = 30) -> dict:
    """Async implementation of cleaning soft-deleted records."""
    from app.models.user import User
    from app.models.category import Category
    from app.models.event import Event
    from app.models.conversation import Conversation
    from app.models.memory import UserMemory

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    total_deleted = 0

    async with async_session_maker() as db:
        try:
            models_to_clean = [
                (User, "users"),
                (Category, "categories"),
                (Event, "events"),
                (Conversation, "conversations"),
                (UserMemory, "user_memory"),
            ]

            for model, table_name in models_to_clean:
                result = await db.execute(
                    delete(model).where(
                        model.deleted_at.is_not(None),
                        model.deleted_at < cutoff_date,
                    )
                )
                deleted = result.rowcount
                total_deleted += deleted
                print(f"Deleted {deleted} records from {table_name}")

            await db.commit()

            return {"total_deleted": total_deleted, "cutoff_date": cutoff_date.isoformat()}

        except Exception as e:
            await db.rollback()
            return {"error": str(e)}


@shared_task
def vacuum_analyze() -> dict:
    """Run VACUUM ANALYZE on database (requires superuser)."""
    # This would need to be run with a superuser connection
    # For now, just return info
    return {"message": "VACUUM ANALYZE requires superuser privileges. Run manually if needed."}