"""Event service."""
from dataclasses import fields
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from dateutil import rrule as rrule_lib
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event, EventReminder, EventStatus, EventPriority
from app.models.category import Category
from app.models.conversation import Conversation
from app.graphql.types.inputs import (
    CreateEventInput,
    UpdateEventInput,
    EventFilterInput,
    BulkUpdateEventInput,
    AIEventProposalInput,
)
from app.graphql.types.event import (
    Event as GQLEvent,
    EventConnection,
    EventEdge,
    PageInfo,
    EventReminder as GQLEventReminder,
)
from app.graphql.types.payloads import ProposedEvent
from app.graphql.serializers import category_to_gql, event_to_gql


class EventService:
    """Event service for managing calendar events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_events(
        self,
        user_id: uuid.UUID,
        filter: Optional[EventFilterInput] = None,
        first: int = 20,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
    ) -> EventConnection:
        """Get paginated events with filtering."""
        query = select(Event).where(
            Event.user_id == user_id,
            Event.deleted_at.is_(None),
        ).options(
            selectinload(Event.category).selectinload(Category.children),
            selectinload(Event.reminders),
        )

        # Apply filters
        if filter:
            query = self._apply_event_filters(query, filter)

        # Order by start_time
        query = query.order_by(Event.start_time)

        # Handle cursor pagination
        if after:
            try:
                after_id = uuid.UUID(after)
                result = await self.db.execute(
                    select(Event.start_time).where(Event.id == after_id)
                )
                after_time = result.scalar_one_or_none()
                if after_time:
                    query = query.where(Event.start_time > after_time)
            except ValueError:
                pass

        if before:
            try:
                before_id = uuid.UUID(before)
                result = await self.db.execute(
                    select(Event.start_time).where(Event.id == before_id)
                )
                before_time = result.scalar_one_or_none()
                if before_time:
                    query = query.where(Event.start_time < before_time)
            except ValueError:
                pass

        # Limit
        limit = min(first or 20, 100)
        if last:
            limit = min(last, 100)
            query = query.order_by(Event.start_time.desc())

        query = query.limit(limit + 1)  # Fetch one extra to check has_next_page

        result = await self.db.execute(query)
        events = result.scalars().all()

        # Check if there are more results
        has_next_page = len(events) > limit
        if has_next_page:
            events = events[:limit]

        # If we used last, reverse the results
        if last:
            events = list(reversed(events))

        # Convert to GraphQL types
        gql_events = [event_to_gql(event) for event in events]

        # Build edges
        edges = [
            EventEdge(node=event, cursor=str(event.id))
            for event in gql_events
        ]

        # Get total count
        count_query = select(func.count(Event.id)).where(
            Event.user_id == user_id,
            Event.deleted_at.is_(None),
        )
        if filter:
            count_query = self._apply_event_filters(count_query, filter)
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar() or 0

        page_info = PageInfo(
            has_next_page=has_next_page,
            has_previous_page=after is not None or before is not None,
            start_cursor=str(edges[0].node.id) if edges else None,
            end_cursor=str(edges[-1].node.id) if edges else None,
        )

        return EventConnection(
            edges=edges,
            page_info=page_info,
            total_count=total_count,
        )

    def _apply_event_filters(self, query, filter: EventFilterInput):
        """Apply event filters to query."""
        if filter.category_ids:
            query = query.where(Event.category_id.in_(filter.category_ids))

        if filter.statuses:
            query = query.where(Event.status.in_(filter.statuses))

        if filter.priorities:
            query = query.where(Event.priority.in_(filter.priorities))

        if filter.start_date:
            query = query.where(Event.end_time >= filter.start_date)

        if filter.end_date:
            query = query.where(Event.start_time <= filter.end_date)

        if filter.search_query:
            search = f"%{filter.search_query}%"
            query = query.where(
                or_(
                    Event.title.ilike(search),
                    Event.description.ilike(search),
                    Event.location.ilike(search),
                )
            )

        if filter.is_recurring is not None:
            query = query.where(Event.is_recurring == filter.is_recurring)

        return query

    async def get_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> Optional[GQLEvent]:
        """Get event by ID."""
        result = await self.db.execute(
            select(Event)
            .where(
                Event.id == event_id,
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
            )
            .options(
                selectinload(Event.category),
                selectinload(Event.reminders),
            )
        )
        event = result.scalar_one_or_none()

        if not event:
            return None

        return event_to_gql(event)

    async def get_upcoming_events(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
        days: int = 30,
    ) -> List[GQLEvent]:
        """Get upcoming events."""
        now = datetime.now(dt_timezone.utc)
        end_date = now + timedelta(days=days)

        result = await self.db.execute(
            select(Event)
            .where(
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
                Event.status == EventStatus.SCHEDULED,
                Event.start_time >= now,
                Event.start_time <= end_date,
            )
            .options(
                selectinload(Event.category),
                selectinload(Event.reminders),
            )
            .order_by(Event.start_time)
            .limit(limit)
        )
        events = result.scalars().all()

        return [event_to_gql(event) for event in events]

    async def get_past_events(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
        days: int = 30,
    ) -> List[GQLEvent]:
        """Get past events."""
        now = datetime.now(dt_timezone.utc)
        start_date = now - timedelta(days=days)

        result = await self.db.execute(
            select(Event)
            .where(
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
                Event.end_time < now,
                Event.end_time >= start_date,
            )
            .options(
                selectinload(Event.category),
                selectinload(Event.reminders),
            )
            .order_by(Event.start_time.desc())
            .limit(limit)
        )
        events = result.scalars().all()

        return [event_to_gql(event) for event in events]

    async def get_events_by_date_range(
        self,
        user_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
        timezone: str = "UTC",
    ) -> List[GQLEvent]:
        """Get events within a date range (including recurring instances)."""
        # Get non-recurring events in range
        result = await self.db.execute(
            select(Event)
            .where(
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
                Event.is_recurring == False,
                Event.start_time < end_date,
                Event.end_time > start_date,
            )
            .options(
                selectinload(Event.category).selectinload(Category.children),
                selectinload(Event.reminders),
            )
        )
        events = result.scalars().all()

        # Get recurring events and expand them
        recurring_result = await self.db.execute(
            select(Event)
            .where(
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
                Event.is_recurring == True,
                Event.rrule.isnot(None),
            )
            .options(
                selectinload(Event.category).selectinload(Category.children),
                selectinload(Event.reminders),
            )
        )
        recurring_events = recurring_result.scalars().all()

        # Expand recurring events and serialize
        all_events = [event_to_gql(event) for event in events]
        for event in recurring_events:
            # Get category data for serialization
            category_data = None
            if event.category:
                category_data = {
                    "id": event.category.id,
                    "user_id": event.category.user_id,
                    "parent_id": event.category.parent_id,
                    "name": event.category.name,
                    "description": event.category.description,
                    "color": event.category.color,
                    "icon": event.category.icon,
                    "is_system": event.category.is_system,
                    "sort_order": event.category.sort_order,
                    "default_reminder_minutes": event.category.default_reminder_minutes,
                    "created_at": event.category.created_at,
                    "updated_at": event.category.updated_at,
                }

            # Get reminders data for serialization
            reminders_data = []
            if event.reminders:
                for reminder in event.reminders:
                    reminders_data.append({
                        "id": reminder.id,
                        "event_id": reminder.event_id,
                        "user_id": reminder.user_id,
                        "minutes_before": reminder.minutes_before,
                        "notification_type": reminder.notification_type,
                        "is_sent": reminder.is_sent,
                        "sent_at": reminder.sent_at,
                        "created_at": reminder.created_at,
                    })

            instances = self._expand_recurring_event(event, start_date, end_date, timezone)
            for instance in instances:
                all_events.append(event_to_gql(instance, reminders_data, category_data))

        # Sort by start time
        all_events.sort(key=lambda e: e.start_time)

        return all_events

    async def get_recurring_instances(
        self,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
        timezone: str = "UTC",
    ) -> List[GQLEvent]:
        """Get instances of a recurring event within a range."""
        result = await self.db.execute(
            select(Event)
            .where(
                Event.id == event_id,
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
                Event.is_recurring == True,
            )
            .options(
                selectinload(Event.category),
                selectinload(Event.reminders),
            )
        )
        event = result.scalar_one_or_none()

        if not event:
            return []

        instances = self._expand_recurring_event(event, start_date, end_date, timezone)
        return [event_to_gql(inst) for inst in instances]

    def _expand_recurring_event(
        self,
        event: Event,
        start_date: datetime,
        end_date: datetime,
        timezone: str,
    ) -> List[Event]:
        """Expand a recurring event into instances within the date range.

        Occurrences listed in ``recurrence_exceptions`` are skipped. Exceptions
        store occurrence timestamps (timezone-aware), not event IDs.
        """
        if not event.rrule:
            return []

        def _as_utc(value: datetime) -> datetime:
            if value.tzinfo is None:
                return value.replace(tzinfo=dt_timezone.utc)
            return value.astimezone(dt_timezone.utc)

        exception_starts = {_as_utc(value) for value in (event.recurrence_exceptions or [])}

        try:
            rule = rrule_lib.rrulestr(event.rrule, dtstart=event.start_time)
            occurrences = rule.between(start_date, end_date, inc=True)
        except (ValueError, TypeError):
            return []

        duration = event.end_time - event.start_time
        instances = []
        for occ in occurrences:
            occurrence_start = _as_utc(occ)
            if occurrence_start in exception_starts:
                continue

            instance = Event(
                id=uuid.uuid4(),
                user_id=event.user_id,
                category_id=event.category_id,
                title=event.title,
                description=event.description,
                location=event.location,
                start_time=occ,
                end_time=occ + duration,
                all_day=event.all_day,
                timezone=event.timezone,
                priority=event.priority,
                status=event.status,
                is_recurring=False,
                rrule=None,
                rrule_original_start=event.start_time,
                recurrence_exceptions=[],
                preparation_notes=event.preparation_notes,
                created_at=event.created_at,
                updated_at=event.updated_at,
            )
            instances.append(instance)

        return instances

    async def create_event(self, user_id: uuid.UUID, input: CreateEventInput) -> GQLEvent:
        """Create a new event."""
        from app.models.event import EventReminder
        from app.models.category import Category

        # Verify category exists and belongs to user
        category = None
        if input.category_id:
            result = await self.db.execute(
                select(Category).where(
                    Category.id == input.category_id,
                    Category.user_id == user_id,
                    Category.deleted_at.is_(None),
                )
            )
            category = result.scalar_one_or_none()
            if not category:
                raise ValueError("Category not found")

        event = Event(
            user_id=user_id,
            category_id=input.category_id,
            title=input.title,
            description=input.description,
            location=input.location,
            start_time=input.start_time,
            end_time=input.end_time,
            all_day=input.all_day,
            timezone=input.timezone,
            priority=input.priority,
            status=input.status,
            is_recurring=input.is_recurring,
            rrule=input.rrule,
            preparation_notes=input.preparation_notes,
        )

        self.db.add(event)
        await self.db.flush()

        # Create reminders and build plain dicts for serialization (avoid SQLAlchemy objects)
        reminders_data = []
        if input.reminders:
            for reminder_input in input.reminders:
                reminder = EventReminder(
                    event_id=event.id,
                    user_id=user_id,
                    minutes_before=reminder_input.minutes_before,
                    notification_type=reminder_input.notification_type,
                )
                self.db.add(reminder)
                await self.db.flush()
                # Build plain dict for serialization
                reminders_data.append({
                    "id": reminder.id,
                    "event_id": reminder.event_id,
                    "user_id": reminder.user_id,
                    "minutes_before": reminder.minutes_before,
                    "notification_type": reminder.notification_type,
                    "is_sent": reminder.is_sent,
                    "sent_at": reminder.sent_at,
                    "created_at": reminder.created_at,
                })

        await self.db.flush()

        # Build plain category dict if available (to avoid lazy loading children)
        category_data = None
        if category:
            category_data = {
                "id": category.id,
                "user_id": category.user_id,
                "parent_id": category.parent_id,
                "name": category.name,
                "description": category.description,
                "color": category.color,
                "icon": category.icon,
                "is_system": category.is_system,
                "sort_order": category.sort_order,
                "default_reminder_minutes": category.default_reminder_minutes,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
            }

        # Serialize with manually provided reminders and category data to avoid lazy loading
        return event_to_gql(event, reminders_data, category_data)

    async def update_event(
        self,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        input: UpdateEventInput,
    ) -> GQLEvent:
        """Update an event."""
        result = await self.db.execute(
            select(Event)
            .where(
                Event.id == event_id,
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
            )
            .options(
                selectinload(Event.category),
                selectinload(Event.reminders),
            )
        )
        event = result.scalar_one_or_none()

        if not event:
            raise ValueError("Event not found")

        # Update fields
        update_data = {
            field.name: getattr(input, field.name)
            for field in fields(input)
            if getattr(input, field.name) is not None
        }
        for field, value in update_data.items():
            setattr(event, field, value)

        await self.db.commit()
        await self.db.refresh(event)

        return event_to_gql(event)

    async def delete_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> bool:
        """Delete an event (soft delete)."""
        result = await self.db.execute(
            select(Event).where(
                Event.id == event_id,
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
            )
        )
        event = result.scalar_one_or_none()

        if not event:
            raise ValueError("Event not found")

        event.deleted_at = datetime.now(dt_timezone.utc)
        await self.db.commit()
        return True

    async def duplicate_event(
        self,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        new_start_time: datetime,
    ) -> GQLEvent:
        """Duplicate an event to a new date."""
        result = await self.db.execute(
            select(Event)
            .where(
                Event.id == event_id,
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
            )
            .options(
                selectinload(Event.category),
                selectinload(Event.reminders),
            )
        )
        event = result.scalar_one_or_none()

        if not event:
            raise ValueError("Event not found")

        # Calculate duration
        duration = event.end_time - event.start_time
        new_end_time = new_start_time + duration

        new_event = Event(
            user_id=user_id,
            category_id=event.category_id,
            title=event.title,
            description=event.description,
            location=event.location,
            start_time=new_start_time,
            end_time=new_end_time,
            all_day=event.all_day,
            timezone=event.timezone,
            priority=event.priority,
            status=EventStatus.SCHEDULED,
            is_recurring=False,
            preparation_notes=event.preparation_notes,
        )

        self.db.add(new_event)
        await self.db.flush()

        # Copy reminders
        for reminder in event.reminders:
            new_reminder = EventReminder(
                event_id=new_event.id,
                user_id=user_id,
                minutes_before=reminder.minutes_before,
                notification_type=reminder.notification_type,
            )
            self.db.add(new_reminder)

        await self.db.commit()
        await self.db.refresh(new_event)

        return event_to_gql(new_event)

    async def complete_event(self, user_id: uuid.UUID, event_id: uuid.UUID) -> GQLEvent:
        """Mark event as completed."""
        result = await self.db.execute(
            select(Event)
            .where(
                Event.id == event_id,
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
            )
            .options(
                selectinload(Event.category),
                selectinload(Event.reminders),
            )
        )
        event = result.scalar_one_or_none()

        if not event:
            raise ValueError("Event not found")

        event.status = EventStatus.COMPLETED
        event.completed_at = datetime.now(dt_timezone.utc)

        await self.db.commit()
        await self.db.refresh(event)

        return event_to_gql(event)

    async def bulk_create_events(
        self,
        user_id: uuid.UUID,
        inputs: List[CreateEventInput],
    ) -> List[GQLEvent]:
        """Create multiple events."""
        events = []
        for input in inputs:
            event = await self.create_event(user_id, input)
            events.append(event)
        return events

    async def bulk_update_events(
        self,
        user_id: uuid.UUID,
        inputs: List[BulkUpdateEventInput],
    ) -> List[GQLEvent]:
        """Update multiple events."""
        events = []
        for input in inputs:
            event = await self.update_event(user_id, input.id, input.input)
            events.append(event)
        return events

    async def bulk_delete_events(
        self,
        user_id: uuid.UUID,
        ids: List[uuid.UUID],
    ) -> bool:
        """Delete multiple events."""
        result = await self.db.execute(
            select(Event).where(
                Event.id.in_(ids),
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
            )
        )
        events = result.scalars().all()

        for event in events:
            event.deleted_at = datetime.now(dt_timezone.utc)

        await self.db.commit()
        return True

    async def create_recurring_exception(
        self,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        exception_date: datetime,
        input: CreateEventInput,
    ) -> GQLEvent:
        """Create an exception for a recurring event."""
        result = await self.db.execute(
            select(Event)
            .where(
                Event.id == event_id,
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
                Event.is_recurring == True,
            )
        )
        master_event = result.scalar_one_or_none()

        if not master_event:
            raise ValueError("Recurring event not found")

        # Create exception event
        exception_event = await self.create_event(user_id, input)

        # Record the skipped occurrence timestamp on the master event.
        exception_start = exception_date
        if exception_start.tzinfo is None:
            exception_start = exception_start.replace(tzinfo=dt_timezone.utc)
        master_event.recurrence_exceptions = list(master_event.recurrence_exceptions or []) + [
            exception_start
        ]

        await self.db.commit()

        return exception_event

    async def update_recurring_series(
        self,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        input: UpdateEventInput,
    ) -> GQLEvent:
        """Update entire recurring series (master event)."""
        result = await self.db.execute(
            select(Event)
            .where(
                Event.id == event_id,
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
                Event.is_recurring == True,
            )
            .options(
                selectinload(Event.category),
                selectinload(Event.reminders),
            )
        )
        master_event = result.scalar_one_or_none()

        if not master_event:
            raise ValueError("Recurring event not found")

        # Update master event
        update_data = {
            field.name: getattr(input, field.name)
            for field in fields(input)
            if getattr(input, field.name) is not None
        }
        for field, value in update_data.items():
            setattr(master_event, field, value)

        await self.db.commit()
        await self.db.refresh(master_event)

        return event_to_gql(master_event)

    async def delete_recurring_series(
        self,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        delete_future: bool = True,
    ) -> bool:
        """Delete recurring series."""
        result = await self.db.execute(
            select(Event)
            .where(
                Event.id == event_id,
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
                Event.is_recurring == True,
            )
        )
        master_event = result.scalar_one_or_none()

        if not master_event:
            raise ValueError("Recurring event not found")

        if delete_future:
            # Soft delete master; occurrences are generated from rrule, so this
            # removes the whole future series.
            master_event.deleted_at = datetime.now(dt_timezone.utc)
        else:
            # Only delete master, keep past instances
            master_event.is_recurring = False
            master_event.rrule = None

        await self.db.commit()
        return True

    async def get_calendar_events(
        self,
        user_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> List[GQLEvent]:
        """Get scheduled events overlapping a calendar range."""
        result = await self.db.execute(
            select(Event)
            .where(
                Event.user_id == user_id,
                Event.deleted_at.is_(None),
                Event.status == EventStatus.SCHEDULED,
                Event.start_time < end_date,
                Event.end_time > start_date,
            )
            .options(
                selectinload(Event.category).selectinload(Category.children),
                selectinload(Event.reminders),
            )
            .order_by(Event.start_time)
        )
        return [event_to_gql(event) for event in result.scalars().all()]

    async def get_today_events(self, user_id: uuid.UUID) -> List[GQLEvent]:
        """Get today's scheduled events (UTC day boundaries)."""
        now = datetime.now(dt_timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return await self.get_calendar_events(user_id, start, end)

    async def get_this_week_events(self, user_id: uuid.UUID) -> List[GQLEvent]:
        """Get this week's scheduled events (UTC, week starts Monday)."""
        now = datetime.now(dt_timezone.utc)
        start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=7)
        return await self.get_calendar_events(user_id, start, end)

    async def get_this_month_events(self, user_id: uuid.UUID) -> List[GQLEvent]:
        """Get this month's scheduled events (UTC month boundaries)."""
        now = datetime.now(dt_timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end = start.replace(year=now.year + 1, month=1)
        else:
            end = start.replace(month=now.month + 1)
        return await self.get_calendar_events(user_id, start, end)

    async def _require_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Conversation:
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise ValueError("Conversation not found")
        return conversation

    async def propose_events(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        proposal: AIEventProposalInput,
    ) -> List[ProposedEvent]:
        """Build ephemeral event proposals from an AI planner suggestion."""
        await self._require_conversation(user_id, conversation_id)

        category = None
        if proposal.category_id:
            result = await self.db.execute(
                select(Category).where(
                    Category.id == proposal.category_id,
                    Category.user_id == user_id,
                    Category.deleted_at.is_(None),
                )
            )
            category = result.scalar_one_or_none()

        now = datetime.now(dt_timezone.utc)
        proposed: List[ProposedEvent] = []
        for suggested_start in proposal.suggested_dates:
            start = suggested_start
            if start.tzinfo is None:
                start = start.replace(tzinfo=dt_timezone.utc)
            end = start + timedelta(minutes=proposal.duration_minutes)
            proposal_id = uuid.uuid4()

            reminders = [
                GQLEventReminder(
                    id=uuid.uuid4(),
                    event_id=proposal_id,
                    user_id=user_id,
                    minutes_before=reminder.minutes_before,
                    notification_type=reminder.notification_type,
                    is_sent=False,
                    sent_at=None,
                    created_at=now,
                )
                for reminder in (proposal.reminders or [])
            ]

            proposed.append(
                ProposedEvent(
                    id=proposal_id,
                    title=proposal.title,
                    description=proposal.description,
                    suggested_start_time=start,
                    suggested_end_time=end,
                    category=category_to_gql(category) if category else None,
                    priority=proposal.priority,
                    preparation_notes=proposal.preparation_notes,
                    reminders=reminders,
                )
            )

        return proposed

    async def confirm_proposed_events(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        event_ids: List[uuid.UUID],
    ) -> List[GQLEvent]:
        """Confirm proposed events.

        Proposals are currently ephemeral, so there is no persisted payload to
        materialise. Kept as a valid no-op until proposal persistence lands.
        """
        await self._require_conversation(user_id, conversation_id)
        return []

    async def reject_proposed_events(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        event_ids: List[uuid.UUID],
    ) -> bool:
        """Reject proposed events."""
        await self._require_conversation(user_id, conversation_id)
        return True
