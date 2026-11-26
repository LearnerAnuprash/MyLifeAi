"""Minimal backend integration tests for core service contracts."""
from datetime import datetime, timedelta, timezone
import uuid

import pytest

from app.graphql.types.inputs import (
    CreateCategoryInput,
    CreateEventInput,
    LoginInput,
    RegisterInput,
    UpdateEventInput,
)
from app.models.event import Event
from app.models.notification import NotificationCategory
from app.services.auth import AuthService
from app.services.category import CategoryService
from app.services.event import EventService
from app.services.notification import NotificationService


async def register_user(db, email: str = "user@example.com"):
    auth = AuthService(db)
    payload = await auth.register(
        RegisterInput(email=email, password="password123", full_name="Test User")
    )
    return auth, payload


async def test_register_login_and_refresh(db):
    auth, payload = await register_user(db)

    assert payload.token
    assert payload.refresh_token
    assert payload.user.email == "user@example.com"

    login = await auth.login(LoginInput(email="user@example.com", password="password123"))
    assert login.token
    assert login.refresh_token

    refreshed = await auth.refresh_token(login.refresh_token)
    assert refreshed

    with pytest.raises(ValueError):
        await auth.register(
            RegisterInput(email="user@example.com", password="password123", full_name="Duplicate")
        )


async def test_event_crud(db):
    _, payload = await register_user(db)
    service = EventService(db)
    start = datetime(2030, 1, 1, 10, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)

    created = await service.create_event(
        payload.user.id,
        CreateEventInput(
            title="Dentist appointment",
            start_time=start,
            end_time=end,
            timezone="UTC",
        ),
    )
    assert created.title == "Dentist appointment"

    fetched = await service.get_event(payload.user.id, created.id)
    assert fetched is not None
    assert fetched.id == created.id

    updated = await service.update_event(
        payload.user.id,
        created.id,
        UpdateEventInput(title="Dentist appointment (moved)"),
    )
    assert updated.title == "Dentist appointment (moved)"

    assert await service.delete_event(payload.user.id, created.id) is True
    assert await service.get_event(payload.user.id, created.id) is None


async def test_category_tree_contains_created_child(db):
    _, payload = await register_user(db)
    service = CategoryService(db)

    tree = await service.get_category_tree(payload.user.id)
    assert tree.categories
    assert len(tree.flat_list) >= len(tree.categories)

    root = await service.create_category(
        payload.user.id,
        CreateCategoryInput(name="Hobbies", color="#123456"),
    )
    child = await service.create_category(
        payload.user.id,
        CreateCategoryInput(name="Cycling", color="#654321", parent_id=root.id),
    )

    updated_tree = await service.get_category_tree(payload.user.id)
    hobby_root = next(category for category in updated_tree.categories if category.id == root.id)
    assert [category.id for category in hobby_root.children] == [child.id]


async def test_notification_unread_count(db):
    _, payload = await register_user(db)
    service = NotificationService(db)

    await service.create_notification(
        payload.user.id,
        NotificationCategory.REMINDER,
        "First reminder",
    )
    second = await service.create_notification(
        payload.user.id,
        NotificationCategory.AI_SUGGESTION,
        "Second reminder",
    )

    assert await service.get_unread_count(payload.user.id) == 2

    await service.mark_read(payload.user.id, second.id)
    assert await service.get_unread_count(payload.user.id) == 1

    await service.mark_all_read(payload.user.id)
    assert await service.get_unread_count(payload.user.id) == 0


async def test_recurring_exception_skips_occurrence(db):
    _, payload = await register_user(db)
    service = EventService(db)
    start = datetime(2030, 1, 1, 10, 0, tzinfo=timezone.utc)

    master = await service.create_event(
        payload.user.id,
        CreateEventInput(
            title="Daily standup",
            start_time=start,
            end_time=start + timedelta(minutes=30),
            timezone="UTC",
            is_recurring=True,
            rrule="FREQ=DAILY;COUNT=3",
        ),
    )

    exception_start = start + timedelta(days=1)
    await service.create_recurring_exception(
        payload.user.id,
        master.id,
        exception_start,
        CreateEventInput(
            title="Daily standup (moved)",
            start_time=exception_start,
            end_time=exception_start + timedelta(minutes=30),
            timezone="UTC",
        ),
    )

    db_master = await db.get(Event, uuid.UUID(str(master.id)))
    await db.refresh(db_master)
    assert db_master is not None
    assert len(db_master.recurrence_exceptions) == 1
    assert isinstance(db_master.recurrence_exceptions[0], datetime)

    events = await service.get_events_by_date_range(
        payload.user.id,
        start - timedelta(hours=1),
        start + timedelta(days=5),
    )
    assert len([event for event in events if event.title == "Daily standup"]) == 2
