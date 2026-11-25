"""Celery application configuration."""
from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "mylife",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks.reminders",
        "app.workers.tasks.notifications",
        "app.workers.tasks.maintenance",
    ],
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_TIME_LIMIT - 30,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=1000,
    result_expires=3600,
    result_compression="gzip",
    task_routes={
        "app.workers.tasks.reminders.*": {"queue": "reminders"},
        "app.workers.tasks.notifications.*": {"queue": "notifications"},
        "app.workers.tasks.maintenance.*": {"queue": "maintenance"},
    },
    task_default_queue="default",
    task_create_missing_queues=True,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Check for due reminders every minute
    "check-due-reminders": {
        "task": "app.workers.tasks.reminders.check_due_reminders",
        "schedule": 60.0,  # Every minute
    },
    # Send upcoming event summaries daily at 8 AM UTC
    "daily-upcoming-summary": {
        "task": "app.workers.tasks.notifications.send_daily_summary",
        "schedule": crontab(hour=8, minute=0),
    },
    # Clean up old sent reminders weekly
    "cleanup-old-reminders": {
        "task": "app.workers.tasks.maintenance.cleanup_old_reminders",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
    },
    # Clean up old notifications monthly
    "cleanup-old-notifications": {
        "task": "app.workers.tasks.maintenance.cleanup_old_notifications",
        "schedule": crontab(day_of_month=1, hour=4, minute=0),  # 1st of month 4 AM
    },
}