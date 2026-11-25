"""User model."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, func, Index, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.event import Event, EventStatus, EventPriority


class User(Base):
    """User model."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC",
    )
    locale: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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

    async def to_gql(self):
        """Convert to GraphQL User type."""
        from app.graphql.types.user import User as GQLUser, UserSettings as GQLUserSettings
        
        # Build settings if available
        settings = None
        if self.settings:
            settings = GQLUserSettings(
                theme=self.settings.theme,
                calendar_default_view=self.settings.calendar_default_view,
                week_start_day=self.settings.week_start_day,
                default_reminder_minutes=self.settings.default_reminder_minutes,
                notification_email=self.settings.notification_email,
                notification_push=self.settings.notification_push,
                ai_provider=self.settings.ai_provider,
                ai_model=self.settings.ai_model,
                language=self.settings.language,
                date_format=self.settings.date_format,
                time_format=self.settings.time_format,
            )
        else:
            # Default settings
            settings = GQLUserSettings(
                theme="system",
                calendar_default_view="week",
                week_start_day=0,
                default_reminder_minutes=[1440, 60, 15],
                notification_email=True,
                notification_push=True,
                ai_provider="openai",
                ai_model="gpt-4o",
                language="en",
                date_format="YYYY-MM-DD",
                time_format="HH:mm",
            )

        return GQLUser(
            id=self.id,
            email=self.email,
            full_name=self.full_name,
            avatar_url=self.avatar_url,
            timezone=self.timezone,
            locale=self.locale,
            is_active=self.is_active,
            is_verified=self.is_verified,
            created_at=self.created_at,
            updated_at=self.updated_at,
            settings=settings,
        )

    # Category methods
    async def get_category_tree(self):
        """Get user's category tree."""
        from app.models.category import Category
        from sqlalchemy import select, func
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            # Get all categories for user
            result = await db.execute(
                select(Category)
                .where(Category.user_id == self.id, Category.deleted_at.is_(None))
                .order_by(Category.sort_order, Category.name)
                .options(selectinload(Category.children))
            )
            categories = result.scalars().all()

            # Build tree
            category_map = {cat.id: cat for cat in categories}
            roots = []

            for cat in categories:
                if cat.parent_id is None:
                    roots.append(cat)
                elif cat.parent_id in category_map:
                    parent = category_map[cat.parent_id]
                    # Children are already loaded via selectinload

            # Convert to GraphQL types
            from app.graphql.types.category import Category as GQLCategory, CategoryTree

            async def cat_to_gql(cat):
                children = []
                if cat.children:
                    for child in cat.children:
                        if child.deleted_at is None:
                            children.append(await cat_to_gql(child))

                return GQLCategory(
                    id=cat.id,
                    user_id=cat.user_id,
                    parent_id=cat.parent_id,
                    name=cat.name,
                    description=cat.description,
                    color=cat.color,
                    icon=cat.icon,
                    is_system=cat.is_system,
                    sort_order=cat.sort_order,
                    default_reminder_minutes=cat.default_reminder_minutes,
                    children=children,
                    created_at=cat.created_at,
                    updated_at=cat.updated_at,
                )

            gql_categories = [await cat_to_gql(cat) for cat in categories]
            gql_roots = [await cat_to_gql(cat) for cat in roots]

            return CategoryTree(
                categories=gql_roots,
                flat_list=gql_categories,
            )

    async def get_category(self, category_id: uuid.UUID):
        """Get category by ID."""
        from app.models.category import Category
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Category)
                .where(
                    Category.id == category_id,
                    Category.user_id == self.id,
                    Category.deleted_at.is_(None),
                )
                .options(selectinload(Category.children))
            )
            category = result.scalar_one_or_none()

            if not category:
                return None

            from app.graphql.types.category import Category as GQLCategory
            return GQLCategory(
                id=category.id,
                user_id=category.user_id,
                parent_id=category.parent_id,
                name=category.name,
                description=category.description,
                color=category.color,
                icon=category.icon,
                is_system=category.is_system,
                sort_order=category.sort_order,
                default_reminder_minutes=category.default_reminder_minutes,
                children=[],
                created_at=category.created_at,
                updated_at=category.updated_at,
            )

    async def create_category(self, input):
        """Create a new category."""
        from app.models.category import Category
        from sqlalchemy import select, func
        from app.db.session import get_db

        async with get_db() as db:
            # Verify parent exists and belongs to user
            if input.parent_id:
                result = await db.execute(
                    select(Category).where(
                        Category.id == input.parent_id,
                        Category.user_id == self.id,
                        Category.deleted_at.is_(None),
                    )
                )
                parent = result.scalar_one_or_none()
                if not parent:
                    raise ValueError("Parent category not found")

            # Get max sort_order for this level
            if input.parent_id:
                result = await db.execute(
                    select(func.max(Category.sort_order))
                    .where(Category.parent_id == input.parent_id, Category.deleted_at.is_(None))
                )
            else:
                result = await db.execute(
                    select(func.max(Category.sort_order))
                    .where(Category.parent_id.is_(None), Category.user_id == self.id, Category.deleted_at.is_(None))
                )
            max_sort = result.scalar() or -1

            category = Category(
                user_id=self.id,
                parent_id=input.parent_id,
                name=input.name,
                description=input.description,
                color=input.color,
                icon=input.icon,
                default_reminder_minutes=input.default_reminder_minutes or [1440, 60, 15],
                sort_order=max_sort + 1,
            )

            db.add(category)
            await db.commit()
            await db.refresh(category)

            from app.graphql.types.category import Category as GQLCategory
            return GQLCategory(
                id=category.id,
                user_id=category.user_id,
                parent_id=category.parent_id,
                name=category.name,
                description=category.description,
                color=category.color,
                icon=category.icon,
                is_system=category.is_system,
                sort_order=category.sort_order,
                default_reminder_minutes=category.default_reminder_minutes,
                children=[],
                created_at=category.created_at,
                updated_at=category.updated_at,
            )

    async def update_category(self, category_id: uuid.UUID, input):
        """Update a category."""
        from app.models.category import Category
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Category)
                .where(
                    Category.id == category_id,
                    Category.user_id == self.id,
                    Category.deleted_at.is_(None),
                )
                .options(selectinload(Category.children))
            )
            category = result.scalar_one_or_none()

            if not category:
                raise ValueError("Category not found")

            if category.is_system:
                raise ValueError("Cannot modify system categories")

            update_data = {k: v for k, v in __import__('strawberry').asdict(input).items() if v is not None}
            for field, value in update_data.items():
                setattr(category, field, value)

            await db.commit()
            await db.refresh(category)

            from app.graphql.types.category import Category as GQLCategory
            return GQLCategory(
                id=category.id,
                user_id=category.user_id,
                parent_id=category.parent_id,
                name=category.name,
                description=category.description,
                color=category.color,
                icon=category.icon,
                is_system=category.is_system,
                sort_order=category.sort_order,
                default_reminder_minutes=category.default_reminder_minutes,
                children=[],
                created_at=category.created_at,
                updated_at=category.updated_at,
            )

    async def delete_category(self, category_id: uuid.UUID) -> bool:
        """Delete a category."""
        from app.models.category import Category
        from sqlalchemy import select
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Category).where(
                    Category.id == category_id,
                    Category.user_id == self.id,
                    Category.deleted_at.is_(None),
                )
            )
            category = result.scalar_one_or_none()

            if not category:
                raise ValueError("Category not found")

            if category.is_system:
                raise ValueError("Cannot delete system categories")

            category.deleted_at = datetime.utcnow()
            await db.commit()
            return True

    async def reorder_categories(self, category_ids: list[uuid.UUID]) -> list:
        """Reorder categories."""
        from app.models.category import Category
        from sqlalchemy import select
        from app.db.session import get_db

        async with get_db() as db:
            # Verify all categories belong to user
            result = await db.execute(
                select(Category).where(
                    Category.id.in_(category_ids),
                    Category.user_id == self.id,
                    Category.deleted_at.is_(None),
                )
            )
            categories = {cat.id: cat for cat in result.scalars().all()}

            if len(categories) != len(category_ids):
                raise ValueError("One or more categories not found")

            # Update sort_order
            for index, cat_id in enumerate(category_ids):
                categories[cat_id].sort_order = index

            await db.commit()

            # Return updated categories
            from app.graphql.types.category import Category as GQLCategory
            gql_categories = []
            for cat_id in category_ids:
                await db.refresh(categories[cat_id])
                gql_categories.append(GQLCategory(
                    id=categories[cat_id].id,
                    user_id=categories[cat_id].user_id,
                    parent_id=categories[cat_id].parent_id,
                    name=categories[cat_id].name,
                    description=categories[cat_id].description,
                    color=categories[cat_id].color,
                    icon=categories[cat_id].icon,
                    is_system=categories[cat_id].is_system,
                    sort_order=categories[cat_id].sort_order,
                    default_reminder_minutes=categories[cat_id].default_reminder_minutes,
                    children=[],
                    created_at=categories[cat_id].created_at,
                    updated_at=categories[cat_id].updated_at,
                ))
            return gql_categories

    # Event methods
    async def get_events(self, filter=None, first=20, after=None, last=None, before=None):
        """Get paginated events with filtering."""
        from app.models.event import Event, EventStatus, EventPriority
        from sqlalchemy import select, func
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db
        from app.graphql.types.event import Event as GQLEvent, EventConnection, EventEdge, PageInfo
        import base64

        async with get_db() as db:
            query = select(Event).where(
                Event.user_id == self.id,
                Event.deleted_at.is_(None),
            ).options(
                selectinload(Event.category),
                selectinload(Event.reminders),
            )

            # Apply filters
            if filter:
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
                        Event.title.ilike(search) |
                        Event.description.ilike(search) |
                        Event.location.ilike(search)
                    )
                if filter.is_recurring is not None:
                    query = query.where(Event.is_recurring == filter.is_recurring)

            # Order by start_time
            query = query.order_by(Event.start_time)

            # Cursor pagination
            if after:
                try:
                    cursor_data = base64.b64decode(after).decode()
                    cursor_time = datetime.fromisoformat(cursor_data)
                    query = query.where(Event.start_time > cursor_time)
                except:
                    pass

            if before:
                try:
                    cursor_data = base64.b64decode(before).decode()
                    cursor_time = datetime.fromisoformat(cursor_data)
                    query = query.where(Event.start_time < cursor_time)
                except:
                    pass

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total_count = total_result.scalar() or 0

            # Apply pagination
            if first:
                query = query.limit(first + 1)
            elif last:
                query = query.limit(last + 1).order_by(Event.start_time.desc())

            result = await db.execute(query)
            events = result.scalars().all()

            # Handle last pagination
            if last:
                events = list(reversed(events))
                if len(events) > last:
                    events = events[:last]

            has_next_page = len(events) > first if first else False
            if has_next_page:
                events = events[:first]

            # Build edges
            edges = []
            for event in events:
                from app.graphql.types.event import Event as GQLEvent
                gql_event = GQLEvent(
                    id=event.id,
                    user_id=event.user_id,
                    category=None,
                    title=event.title,
                    description=event.description,
                    location=event.location,
                    start_time=event.start_time,
                    end_time=event.end_time,
                    all_day=event.all_day,
                    timezone=event.timezone,
                    priority=event.priority,
                    status=event.status,
                    is_recurring=event.is_recurring,
                    rrule=event.rrule,
                    rrule_original_start=event.rrule_original_start,
                    recurrence_exceptions=event.recurrence_exceptions,
                    preparation_notes=event.preparation_notes,
                    completed_at=event.completed_at,
                    created_at=event.created_at,
                    updated_at=event.updated_at,
                    reminders=[],
                )
                cursor = base64.b64encode(event.start_time.isoformat().encode()).decode()
                edges.append(EventEdge(node=gql_event, cursor=cursor))

            # Page info
            page_info = PageInfo(
                has_next_page=has_next_page,
                has_previous_page=after is not None or before is not None,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            )

            return EventConnection(
                edges=edges,
                page_info=page_info,
                total_count=total_count,
            )

    async def get_event(self, event_id: uuid.UUID):
        """Get event by ID."""
        from app.models.event import Event
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Event)
                .where(
                    Event.id == event_id,
                    Event.user_id == self.id,
                    Event.deleted_at.is_(None),
                )
                .options(
                    selectinload(Event.category),
                    selectinload(Event.reminders),
                )
            )
            return result.scalar_one_or_none()

    async def get_upcoming_events(self, limit=10, days=30):
        """Get upcoming events."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db
        from datetime import timedelta

        async with get_db() as db:
            now = datetime.utcnow()
            end_date = now + timedelta(days=days)

            result = await db.execute(
                select(Event)
                .where(
                    Event.user_id == self.id,
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
            return events

    async def get_past_events(self, limit=10, days=30):
        """Get past events."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db
        from datetime import timedelta

        async with get_db() as db:
            now = datetime.utcnow()
            start_date = now - timedelta(days=days)

            result = await db.execute(
                select(Event)
                .where(
                    Event.user_id == self.id,
                    Event.deleted_at.is_(None),
                    Event.status == EventStatus.SCHEDULED,
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
            return events

    async def get_events_by_date_range(self, range):
        """Get events within a date range for calendar views."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Event)
                .where(
                    Event.user_id == self.id,
                    Event.deleted_at.is_(None),
                    Event.start_time < range.end_date,
                    Event.end_time > range.start_date,
                )
                .options(
                    selectinload(Event.category),
                    selectinload(Event.reminders),
                )
                .order_by(Event.start_time)
            )
            events = result.scalars().all()
            return events

    async def get_recurring_instances(self, event_id, range):
        """Get recurring event instances within a range."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db
        import dateutil.rrule as rrule_lib

        async with get_db() as db:
            result = await db.execute(
                select(Event)
                .where(
                    Event.id == event_id,
                    Event.user_id == self.id,
                    Event.deleted_at.is_(None),
                    Event.is_recurring == True,
                    Event.rrule.isnot(None),
                )
                .options(
                    selectinload(Event.category),
                    selectinload(Event.reminders),
                )
            )
            event = result.scalar_one_or_none()

            if not event:
                return []

            try:
                rule = rrule_lib.rrulestr(event.rrule, dtstart=event.start_time)
                occurrences = rule.between(
                    range.start_date,
                    range.end_date,
                    inc=True,
                )

                instances = []
                for occ in occurrences:
                    if event.recurrence_exceptions:
                        pass  # Would need to check exceptions

                    duration = event.end_time - event.start_time
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
                        rrule_original_start=event.rrule_original_start,
                        recurrence_exceptions=event.recurrence_exceptions,
                        preparation_notes=event.preparation_notes,
                        created_at=event.created_at,
                        updated_at=event.updated_at,
                    )
                    instance.category = event.category
                    instance.reminders = event.reminders
                    instances.append(instance)

                return instances
            except Exception:
                return []

    async def create_event(self, input):
        """Create a new event."""
        from app.models.event import Event, EventStatus, EventPriority
        from sqlalchemy import select
        from app.db.session import get_db
        from app.graphql.types.event import Event as GQLEvent
        from app.graphql.types.category import Category as GQLCategory

        async with get_db() as db:
            # Verify category belongs to user
            if input.category_id:
                from app.models.category import Category
                result = await db.execute(
                    select(Category).where(
                        Category.id == input.category_id,
                        Category.user_id == self.id,
                        Category.deleted_at.is_(None),
                    )
                )
                category = result.scalar_one_or_none()
                if not category:
                    raise ValueError("Category not found")

            event = Event(
                user_id=self.id,
                category_id=input.category_id,
                title=input.title,
                description=input.description,
                location=input.location,
                start_time=input.start_time,
                end_time=input.end_time,
                all_day=input.all_day,
                timezone=input.timezone,
                priority=input.priority or EventPriority.NORMAL,
                status=EventStatus.SCHEDULED,
                is_recurring=input.is_recurring or False,
                rrule=input.rrule,
                preparation_notes=input.preparation_notes,
            )

            db.add(event)
            await db.commit()
            await db.refresh(event)

            # Create reminders if provided
            if input.reminders:
                from app.models.event import EventReminder, NotificationType
                for reminder_input in input.reminders:
                    reminder = EventReminder(
                        event_id=event.id,
                        user_id=self.id,
                        minutes_before=reminder_input.minutes_before,
                        notification_type=reminder_input.notification_type,
                    )
                    db.add(reminder)
                await db.commit()
                await db.refresh(event)

            # Load category and reminders
            from sqlalchemy.orm import selectinload
            result = await db.execute(
                select(Event)
                .where(Event.id == event.id)
                .options(
                    selectinload(Event.category),
                    selectinload(Event.reminders),
                )
            )
            event = result.scalar_one()

            # Convert to GraphQL type
            category = None
            if event.category:
                category = GQLCategory(
                    id=event.category.id,
                    user_id=event.category.user_id,
                    parent_id=event.category.parent_id,
                    name=event.category.name,
                    description=event.category.description,
                    color=event.category.color,
                    icon=event.category.icon,
                    is_system=event.category.is_system,
                    sort_order=event.category.sort_order,
                    default_reminder_minutes=event.category.default_reminder_minutes,
                    children=[],
                    created_at=event.category.created_at,
                    updated_at=event.category.updated_at,
                )

            reminders = []
            if event.reminders:
                from app.graphql.types.event import EventReminder
                for reminder in event.reminders:
                    reminders.append(EventReminder(
                        id=reminder.id,
                        event_id=reminder.event_id,
                        user_id=reminder.user_id,
                        minutes_before=reminder.minutes_before,
                        notification_type=reminder.notification_type,
                        is_sent=reminder.is_sent,
                        sent_at=reminder.sent_at,
                        created_at=reminder.created_at,
                    ))

            return GQLEvent(
                id=event.id,
                user_id=event.user_id,
                category=category,
                title=event.title,
                description=event.description,
                location=event.location,
                start_time=event.start_time,
                end_time=event.end_time,
                all_day=event.all_day,
                timezone=event.timezone,
                priority=event.priority,
                status=event.status,
                is_recurring=event.is_recurring,
                rrule=event.rrule,
                rrule_original_start=event.rrule_original_start,
                recurrence_exceptions=event.recurrence_exceptions,
                preparation_notes=event.preparation_notes,
                completed_at=event.completed_at,
                created_at=event.created_at,
                updated_at=event.updated_at,
                reminders=reminders,
            )

    async def update_event(self, id: uuid.UUID, input):
        """Update an event."""
        from app.models.event import Event
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Event)
                .where(
                    Event.id == id,
                    Event.user_id == self.id,
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

            update_data = {k: v for k, v in __import__('strawberry').asdict(input).items() if v is not None}
            for field, value in update_data.items():
                setattr(event, field, value)

            await db.commit()
            await db.refresh(event)

            # Reload with relationships
            result = await db.execute(
                select(Event)
                .where(Event.id == event.id)
                .options(
                    selectinload(Event.category),
                    selectinload(Event.reminders),
                )
            )
            event = result.scalar_one()

            from app.graphql.types.event import Event as GQLEvent
            from app.graphql.types.category import Category as GQLCategory

            category = None
            if event.category:
                category = GQLCategory(
                    id=event.category.id,
                    user_id=event.category.user_id,
                    parent_id=event.category.parent_id,
                    name=event.category.name,
                    description=event.category.description,
                    color=event.category.color,
                    icon=event.category.icon,
                    is_system=event.category.is_system,
                    sort_order=event.category.sort_order,
                    default_reminder_minutes=event.category.default_reminder_minutes,
                    children=[],
                    created_at=event.category.created_at,
                    updated_at=event.category.updated_at,
                )

            reminders = []
            if event.reminders:
                from app.graphql.types.event import EventReminder
                for reminder in event.reminders:
                    reminders.append(EventReminder(
                        id=reminder.id,
                        event_id=reminder.event_id,
                        user_id=reminder.user_id,
                        minutes_before=reminder.minutes_before,
                        notification_type=reminder.notification_type,
                        is_sent=reminder.is_sent,
                        sent_at=reminder.sent_at,
                        created_at=reminder.created_at,
                    ))

            return GQLEvent(
                id=event.id,
                user_id=event.user_id,
                category=category,
                title=event.title,
                description=event.description,
                location=event.location,
                start_time=event.start_time,
                end_time=event.end_time,
                all_day=event.all_day,
                timezone=event.timezone,
                priority=event.priority,
                status=event.status,
                is_recurring=event.is_recurring,
                rrule=event.rrule,
                rrule_original_start=event.rrule_original_start,
                recurrence_exceptions=event.recurrence_exceptions,
                preparation_notes=event.preparation_notes,
                completed_at=event.completed_at,
                created_at=event.created_at,
                updated_at=event.updated_at,
                reminders=reminders,
            )

    async def delete_event(self, id: uuid.UUID) -> bool:
        """Delete an event."""
        from app.models.event import Event
        from sqlalchemy import select
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Event).where(
                    Event.id == id,
                    Event.user_id == self.id,
                    Event.deleted_at.is_(None),
                )
            )
            event = result.scalar_one_or_none()

            if not event:
                raise ValueError("Event not found")

            event.deleted_at = datetime.utcnow()
            await db.commit()
            return True

    async def duplicate_event(self, id: uuid.UUID, new_start_time: datetime) -> Event:
        """Duplicate an event to a new date."""
        from app.models.event import Event
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Event)
                .where(
                    Event.id == id,
                    Event.user_id == self.id,
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

            duration = event.end_time - event.start_time
            new_end_time = new_start_time + duration

            new_event = Event(
                user_id=self.id,
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
                rrule=None,
                preparation_notes=event.preparation_notes,
            )

            db.add(new_event)
            await db.commit()
            await db.refresh(new_event)

            # Copy reminders
            for reminder in event.reminders:
                from app.models.event import EventReminder
                new_reminder = EventReminder(
                    event_id=new_event.id,
                    user_id=self.id,
                    minutes_before=reminder.minutes_before,
                    notification_type=reminder.notification_type,
                )
                db.add(new_reminder)

            await db.commit()
            await db.refresh(new_event)

            # Load relationships
            result = await db.execute(
                select(Event)
                .where(Event.id == new_event.id)
                .options(
                    selectinload(Event.category),
                    selectinload(Event.reminders),
                )
            )
            new_event = result.scalar_one()

            return new_event

    async def complete_event(self, id: uuid.UUID):
        """Mark event as completed."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Event)
                .where(
                    Event.id == id,
                    Event.user_id == self.id,
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
            event.completed_at = datetime.utcnow()

            await db.commit()
            await db.refresh(event)

            from app.graphql.types.event import Event as GQLEvent
            from app.graphql.types.category import Category as GQLCategory

            category = None
            if event.category:
                category = GQLCategory(
                    id=event.category.id,
                    user_id=event.category.user_id,
                    parent_id=event.category.parent_id,
                    name=event.category.name,
                    description=event.category.description,
                    color=event.category.color,
                    icon=event.category.icon,
                    is_system=event.category.is_system,
                    sort_order=event.category.sort_order,
                    default_reminder_minutes=event.category.default_reminder_minutes,
                    children=[],
                    created_at=event.category.created_at,
                    updated_at=event.category.updated_at,
                )

            reminders = []
            if event.reminders:
                from app.graphql.types.event import EventReminder
                for reminder in event.reminders:
                    reminders.append(EventReminder(
                        id=reminder.id,
                        event_id=reminder.event_id,
                        user_id=reminder.user_id,
                        minutes_before=reminder.minutes_before,
                        notification_type=reminder.notification_type,
                        is_sent=reminder.is_sent,
                        sent_at=reminder.sent_at,
                        created_at=reminder.created_at,
                    ))

            return GQLEvent(
                id=event.id,
                user_id=event.user_id,
                category=category,
                title=event.title,
                description=event.description,
                location=event.location,
                start_time=event.start_time,
                end_time=event.end_time,
                all_day=event.all_day,
                timezone=event.timezone,
                priority=event.priority,
                status=event.status,
                is_recurring=event.is_recurring,
                rrule=event.rrule,
                rrule_original_start=event.rrule_original_start,
                recurrence_exceptions=event.recurrence_exceptions,
                preparation_notes=event.preparation_notes,
                completed_at=event.completed_at,
                created_at=event.created_at,
                updated_at=event.updated_at,
                reminders=reminders,
            )

    async def bulk_create_events(self, inputs):
        """Create multiple events."""
        events = []
        for input in inputs:
            event = await self.create_event(input)
            events.append(event)
        return events

    async def bulk_update_events(self, inputs):
        """Update multiple events."""
        events = []
        for input in inputs:
            event = await self.update_event(input.id, input.input)
            events.append(event)
        return events

    async def bulk_delete_events(self, ids: list[uuid.UUID]) -> bool:
        """Delete multiple events."""
        for id in ids:
            await self.delete_event(id)
        return True

    async def create_recurring_exception(self, event_id: uuid.UUID, exception_date: datetime, input):
        """Create an exception for a recurring event."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Event)
                .where(
                    Event.id == event_id,
                    Event.user_id == self.id,
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
                raise ValueError("Recurring event not found")

            if event.recurrence_exceptions is None:
                event.recurrence_exceptions = []

            event.recurrence_exceptions = list(event.recurrence_exceptions) + [exception_date]

            # Create exception event
            exception_event = await self.create_event(input)
            return exception_event

    async def update_recurring_series(self, event_id: uuid.UUID, input):
        """Update entire recurring series."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Event)
                .where(
                    Event.id == event_id,
                    Event.user_id == self.id,
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
                raise ValueError("Recurring event not found")

            # Update the master event
            update_data = {k: v for k, v in __import__('strawberry').asdict(input).items() if v is not None}
            for field, value in update_data.items():
                setattr(event, field, value)

            # Add exception for the updated event
            if event.recurrence_exceptions is None:
                event.recurrence_exceptions = []
            event.recurrence_exceptions = list(event.recurrence_exceptions) + [datetime.utcnow()]

            await db.commit()
            await db.refresh(event)

            from app.graphql.types.event import Event as GQLEvent
            from app.graphql.types.category import Category as GQLCategory

            category = None
            if event.category:
                category = GQLCategory(
                    id=event.category.id,
                    user_id=event.category.user_id,
                    parent_id=event.category.parent_id,
                    name=event.category.name,
                    description=event.category.description,
                    color=event.category.color,
                    icon=event.category.icon,
                    is_system=event.category.is_system,
                    sort_order=event.category.sort_order,
                    default_reminder_minutes=event.category.default_reminder_minutes,
                    children=[],
                    created_at=event.category.created_at,
                    updated_at=event.category.updated_at,
                )

            reminders = []
            if event.reminders:
                from app.graphql.types.event import EventReminder
                for reminder in event.reminders:
                    reminders.append(EventReminder(
                        id=reminder.id,
                        event_id=reminder.event_id,
                        user_id=reminder.user_id,
                        minutes_before=reminder.minutes_before,
                        notification_type=reminder.notification_type,
                        is_sent=reminder.is_sent,
                        sent_at=reminder.sent_at,
                        created_at=reminder.created_at,
                    ))

            return GQLEvent(
                id=event.id,
                user_id=event.user_id,
                category=category,
                title=event.title,
                description=event.description,
                location=event.location,
                start_time=event.start_time,
                end_time=event.end_time,
                all_day=event.all_day,
                timezone=event.timezone,
                priority=event.priority,
                status=event.status,
                is_recurring=event.is_recurring,
                rrule=event.rrule,
                rrule_original_start=event.rrule_original_start,
                recurrence_exceptions=event.recurrence_exceptions,
                preparation_notes=event.preparation_notes,
                completed_at=event.completed_at,
                created_at=event.created_at,
                updated_at=event.updated_at,
                reminders=reminders,
            )

    async def delete_recurring_series(self, event_id: uuid.UUID, delete_future: bool = True) -> bool:
        """Delete recurring series."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Event)
                .where(
                    Event.id == event_id,
                    Event.user_id == self.id,
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
                raise ValueError("Recurring event not found")

            if delete_future:
                event.deleted_at = datetime.utcnow()
            else:
                # Only delete past occurrences
                pass

            await db.commit()
            return True

    # Conversation methods
    async def get_conversations(self, first=20, after=None):
        """Get user's conversations with pagination."""
        from app.models.conversation import Conversation
        from sqlalchemy import select, func
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db
        from app.graphql.types.conversation import ConversationConnection, ConversationEdge, PageInfo
        import base64

        async with get_db() as db:
            query = select(Conversation).where(
                Conversation.user_id == self.id,
                Conversation.deleted_at.is_(None),
            ).options(selectinload(Conversation.messages)).order_by(Conversation.updated_at.desc())

            if after:
                try:
                    cursor_data = base64.b64decode(after).decode()
                    cursor_time = datetime.fromisoformat(cursor_data)
                    query = query.where(Conversation.updated_at < cursor_time)
                except:
                    pass

            query = query.limit(first + 1)
            result = await db.execute(query)
            conversations = result.scalars().all()

            has_next_page = len(conversations) > first
            if has_next_page:
                conversations = conversations[:first]

            edges = []
            for conv in conversations:
                edges.append(ConversationEdge(
                    node=conv,
                    cursor=base64.b64encode(str(conv.updated_at).encode()).decode()
                ))

            page_info = PageInfo(
                has_next_page=has_next_page,
                has_previous_page=after is not None,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            )

            count_query = select(func.count(Conversation.id)).where(
                Conversation.user_id == self.id,
                Conversation.deleted_at.is_(None),
            )
            total_result = await db.execute(count_query)
            total_count = total_result.scalar() or 0

            return ConversationConnection(
                edges=edges,
                page_info=page_info,
                total_count=total_count,
            )

    async def get_conversation(self, conversation_id):
        """Get conversation by ID."""
        from app.models.conversation import Conversation
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Conversation)
                .where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == self.id,
                    Conversation.deleted_at.is_(None),
                )
                .options(selectinload(Conversation.messages))
            )
            return result.scalar_one_or_none()

    async def create_conversation(self, input):
        """Create a new conversation."""
        from app.models.conversation import Conversation
        from app.db.session import get_db
        from app.graphql.types.conversation import Conversation as GQLConversation

        async with get_db() as db:
            conversation = Conversation(
                user_id=self.id,
                title=input.title,
                model_provider=input.model_provider or "openai",
                model_name=input.model_name or "gpt-4o",
                system_prompt=input.system_prompt,
            )

            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)

            return GQLConversation(
                id=conversation.id,
                user_id=conversation.user_id,
                title=conversation.title,
                model_provider=conversation.model_provider,
                model_name=conversation.model_name,
                system_prompt=conversation.system_prompt,
                messages=[],
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )

    async def update_conversation(self, id: uuid.UUID, title: str):
        """Update conversation title."""
        from app.models.conversation import Conversation
        from sqlalchemy import select
        from app.db.session import get_db
        from app.graphql.types.conversation import Conversation as GQLConversation

        async with get_db() as db:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == id,
                    Conversation.user_id == self.id,
                    Conversation.deleted_at.is_(None),
                )
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ValueError("Conversation not found")

            conversation.title = title
            await db.commit()
            await db.refresh(conversation)

            return GQLConversation(
                id=conversation.id,
                user_id=conversation.user_id,
                title=conversation.title,
                model_provider=conversation.model_provider,
                model_name=conversation.model_name,
                system_prompt=conversation.system_prompt,
                messages=[],
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )

    async def delete_conversation(self, id: uuid.UUID) -> bool:
        """Delete a conversation."""
        from app.models.conversation import Conversation
        from sqlalchemy import select
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == id,
                    Conversation.user_id == self.id,
                    Conversation.deleted_at.is_(None),
                )
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ValueError("Conversation not found")

            conversation.deleted_at = datetime.utcnow()
            await db.commit()
            return True

    async def send_message(self, input):
        """Send a message and get AI response with tool calling."""
        from app.models.conversation import Conversation
        from app.models.conversation import Message
        from app.models.conversation import ConversationRole
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db, async_session_maker
        from app.services.ai import AIService, get_planner_response
        from app.graphql.types.conversation import Message as GQLMessage
        from app.graphql.types.payloads import SendMessagePayload

        async with get_db() as db:
            result = await db.execute(
                select(Conversation)
                .where(
                    Conversation.id == input.conversation_id,
                    Conversation.user_id == self.id,
                    Conversation.deleted_at.is_(None),
                )
                .options(selectinload(Conversation.messages))
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ValueError("Conversation not found")

            # Add user message
            user_message = Message(
                conversation_id=conversation.id,
                role=ConversationRole.USER,
                content=input.content,
                tool_calls=None,
                tool_call_id=None,
                metadata=None,
            )
            db.add(user_message)

            # Build messages from conversation history
            messages = []
            if conversation.system_prompt:
                messages.append({"role": "system", "content": conversation.system_prompt})

            # Add conversation history
            for msg in conversation.messages:
                messages.append({"role": msg.role.value, "content": msg.content})

            # Add current message
            messages.append({"role": "user", "content": input.content})

            # Get AI response with tool calling
            ai_service = AIService()

            # Build user context
            user_context = {
                "conversation_id": str(conversation.id),
                "timezone": self.timezone,
                "model_provider": "mock",  # Use mock provider for development
                "model_name": "gpt-4o",
            }

            # Get planner response with tool calling (uses mock provider for development)
            ai_response = await get_planner_response(
                user_message=input.content,
                conversation_history=messages[:-1],  # Exclude current message
                user_context=user_context,
                ai_service=ai_service,
                user_id=self.id,
                db_session_factory=async_session_maker,
            )

            # Add AI message
            ai_message = Message(
                conversation_id=conversation.id,
                role=ConversationRole.ASSISTANT,
                content=ai_response,
                tool_calls=None,
                tool_call_id=None,
                metadata=None,
            )
            db.add(ai_message)

            conversation.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(user_message)
            await db.refresh(ai_message)

            return SendMessagePayload(
                user_message=GQLMessage(
                    id=user_message.id,
                    conversation_id=user_message.conversation_id,
                    role=user_message.role,
                    content=user_message.content,
                    created_at=user_message.created_at,
                ),
                assistant_message=GQLMessage(
                    id=ai_message.id,
                    conversation_id=ai_message.conversation_id,
                    role=ai_message.role,
                    content=ai_message.content,
                    created_at=ai_message.created_at,
                ),
            )

    # Memory methods
    async def get_memories(self, filter=None, first=20, after=None):
        """Get user's memories with pagination."""
        from app.models.memory import UserMemory, MemoryType
        from sqlalchemy import select, func
        from app.db.session import get_db
        from app.graphql.types.memory import MemoryConnection, MemoryEdge, PageInfo
        import base64

        async with get_db() as db:
            query = select(UserMemory).where(
                UserMemory.user_id == self.id,
                UserMemory.deleted_at.is_(None),
            ).order_by(UserMemory.created_at.desc())

            if filter:
                if filter.memory_types:
                    query = query.where(UserMemory.memory_type.in_(filter.memory_types))
                if filter.is_active is not None:
                    query = query.where(UserMemory.is_active == filter.is_active)

            if after:
                try:
                    after_id = uuid.UUID(after)
                    result = await db.execute(
                        select(UserMemory.created_at).where(UserMemory.id == after_id)
                    )
                    after_time = result.scalar_one_or_none()
                    if after_time:
                        query = query.where(UserMemory.created_at < after_time)
                except Exception:
                    pass

            query = query.limit(first + 1)
            result = await db.execute(query)
            memories = result.scalars().all()

            has_next_page = len(memories) > first
            if has_next_page:
                memories = memories[:first]

            edges = []
            for memory in memories:
                edges.append(MemoryEdge(
                    node=memory,
                    cursor=base64.b64encode(str(memory.id).encode()).decode()
                ))

            page_info = PageInfo(
                has_next_page=has_next_page,
                has_previous_page=after is not None,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            )

            count_query = select(func.count(UserMemory.id)).where(
                UserMemory.user_id == self.id,
                UserMemory.deleted_at.is_(None),
            )
            if filter:
                if filter.memory_types:
                    count_query = count_query.where(UserMemory.memory_type.in_(filter.memory_types))
                if filter.is_active is not None:
                    count_query = count_query.where(UserMemory.is_active == filter.is_active)
            total_result = await db.execute(count_query)
            total_count = total_result.scalar() or 0

            return MemoryConnection(
                edges=edges,
                page_info=page_info,
                total_count=total_count,
            )

    async def get_memory(self, memory_id: uuid.UUID):
        """Get memory by ID."""
        from app.models.memory import UserMemory
        from sqlalchemy import select
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(UserMemory).where(
                    UserMemory.id == memory_id,
                    UserMemory.user_id == self.id,
                    UserMemory.deleted_at.is_(None),
                )
            )
            return result.scalar_one_or_none()

    async def search_memory(self, input):
        """Semantic search for memories."""
        from app.models.memory import UserMemory
        from sqlalchemy import select
        from app.db.session import get_db

        async with get_db() as db:
            query = select(UserMemory).where(
                UserMemory.user_id == self.id,
                UserMemory.deleted_at.is_(None),
                UserMemory.is_active == True,
            )

            # Simple text search on title and content
            search_term = f"%{input.query}%"
            query = query.where(
                UserMemory.title.ilike(search_term) |
                UserMemory.content.ilike(search_term)
            )

            if input.memory_types:
                query = query.where(UserMemory.memory_type.in_(input.memory_types))

            query = query.limit(input.limit or 10)

            result = await db.execute(query)
            memories = result.scalars().all()

            return memories

    async def create_memory(self, input):
        """Create a memory entry."""
        from app.models.memory import UserMemory, MemoryType
        from app.db.session import get_db
        from app.graphql.types.memory import UserMemory as GQLUserMemory

        async with get_db() as db:
            # Verify conversation exists if provided
            if input.source_conversation_id:
                from app.models.conversation import Conversation
                result = await db.execute(
                    select(Conversation).where(
                        Conversation.id == input.source_conversation_id,
                        Conversation.user_id == self.id,
                    )
                )
                if not result.scalar_one_or_none():
                    raise ValueError("Source conversation not found")

            memory = UserMemory(
                user_id=self.id,
                memory_type=input.memory_type,
                title=input.title,
                content=input.content,
                source_conversation_id=input.source_conversation_id,
                confidence=input.confidence or 1.0,
            )

            db.add(memory)
            await db.commit()
            await db.refresh(memory)

            return GQLUserMemory(
                id=memory.id,
                user_id=memory.user_id,
                memory_type=memory.memory_type,
                title=memory.title,
                content=memory.content,
                embedding=memory.embedding,
                source_conversation_id=memory.source_conversation_id,
                confidence=memory.confidence,
                is_active=memory.is_active,
                created_at=memory.created_at,
                updated_at=memory.updated_at,
            )

    async def update_memory(self, id: uuid.UUID, input):
        """Update a memory entry."""
        from app.models.memory import UserMemory
        from sqlalchemy import select
        from app.db.session import get_db
        from app.graphql.types.memory import UserMemory as GQLUserMemory

        async with get_db() as db:
            result = await db.execute(
                select(UserMemory).where(
                    UserMemory.id == id,
                    UserMemory.user_id == self.id,
                    UserMemory.deleted_at.is_(None),
                )
            )
            memory = result.scalar_one_or_none()

            if not memory:
                raise ValueError("Memory not found")

            update_data = {k: v for k, v in __import__('strawberry').asdict(input).items() if v is not None}
            for field, value in update_data.items():
                setattr(memory, field, value)

            await db.commit()
            await db.refresh(memory)

            return GQLUserMemory(
                id=memory.id,
                user_id=memory.user_id,
                memory_type=memory.memory_type,
                title=memory.title,
                content=memory.content,
                embedding=memory.embedding,
                source_conversation_id=memory.source_conversation_id,
                confidence=memory.confidence,
                is_active=memory.is_active,
                created_at=memory.created_at,
                updated_at=memory.updated_at,
            )

    async def delete_memory(self, id: uuid.UUID) -> bool:
        """Delete a memory entry."""
        from app.models.memory import UserMemory
        from sqlalchemy import select
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(UserMemory).where(
                    UserMemory.id == id,
                    UserMemory.user_id == self.id,
                    UserMemory.deleted_at.is_(None),
                )
            )
            memory = result.scalar_one_or_none()

            if not memory:
                raise ValueError("Memory not found")

            memory.deleted_at = datetime.utcnow()
            await db.commit()
            return True

    async def bulk_create_memories(self, inputs):
        """Create multiple memory entries."""
        memories = []
        for input in inputs:
            memory = await self.create_memory(input)
            memories.append(memory)
        return memories

    # Notification methods
    async def get_notifications(self, filter=None, first=20, after=None):
        """Get user's notifications."""
        from app.models.notification import Notification, NotificationCategory
        from sqlalchemy import select, func
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db
        from app.graphql.types.notification import NotificationConnection, NotificationEdge, PageInfo
        import base64

        async with get_db() as db:
            query = select(Notification).where(
                Notification.user_id == self.id,
            ).order_by(Notification.created_at.desc())

            if filter:
                if filter.is_read is not None:
                    query = query.where(Notification.is_read == filter.is_read)
                if filter.types:
                    query = query.where(Notification.type.in_(filter.types))

            if after:
                try:
                    after_id = uuid.UUID(after)
                    result = await db.execute(
                        select(Notification.created_at).where(Notification.id == after_id)
                    )
                    after_time = result.scalar_one_or_none()
                    if after_time:
                        query = query.where(Notification.created_at < after_time)
                except:
                    pass

            query = query.limit(first + 1)
            result = await db.execute(query)
            notifications = result.scalars().all()

            has_next_page = len(notifications) > first
            if has_next_page:
                notifications = notifications[:first]

            edges = []
            for notification in notifications:
                edges.append(NotificationEdge(
                    node=notification,
                    cursor=base64.b64encode(str(notification.id).encode()).decode()
                ))

            count_query = select(func.count(Notification.id)).where(
                Notification.user_id == self.id,
            )
            if filter:
                if filter.is_read is not None:
                    count_query = count_query.where(Notification.is_read == filter.is_read)
                if filter.types:
                    count_query = count_query.where(Notification.type.in_(filter.types))

            total_result = await db.execute(count_query)
            total_count = total_result.scalar() or 0

            unread_query = select(func.count(Notification.id)).where(
                Notification.user_id == self.id,
                Notification.is_read == False,
            )
            unread_result = await db.execute(unread_query)
            unread_count = unread_result.scalar() or 0

            page_info = PageInfo(
                has_next_page=has_next_page,
                has_previous_page=after is not None,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            )

            return NotificationConnection(
                edges=edges,
                page_info=page_info,
                total_count=total_count,
                unread_count=unread_count,
            )

    async def get_unread_notification_count(self):
        """Get count of unread notifications."""
        from app.models.notification import Notification
        from sqlalchemy import select, func
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(func.count(Notification.id)).where(
                    Notification.user_id == self.id,
                    Notification.is_read == False,
                )
            )
            return result.scalar() or 0

    async def mark_notification_read(self, id: uuid.UUID):
        """Mark notification as read."""
        from app.models.notification import Notification
        from sqlalchemy import select
        from app.db.session import get_db
        from app.graphql.types.notification import Notification as GQLNotification

        async with get_db() as db:
            result = await db.execute(
                select(Notification).where(
                    Notification.id == id,
                    Notification.user_id == self.id,
                )
            )
            notification = result.scalar_one_or_none()

            if not notification:
                raise ValueError("Notification not found")

            notification.is_read = True
            notification.read_at = datetime.utcnow()

            await db.commit()
            await db.refresh(notification)

            return GQLNotification(
                id=notification.id,
                user_id=notification.user_id,
                type=notification.type,
                title=notification.title,
                body=notification.body,
                reference_id=notification.reference_id,
                reference_type=notification.reference_type,
                is_read=notification.is_read,
                read_at=notification.read_at,
                created_at=notification.created_at,
            )

    async def mark_all_notifications_read(self) -> bool:
        """Mark all notifications as read."""
        from app.models.notification import Notification
        from sqlalchemy import select, update
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Notification).where(
                    Notification.user_id == self.id,
                    Notification.is_read == False,
                )
            )
            notifications = result.scalars().all()

            for notification in notifications:
                notification.is_read = True
                notification.read_at = datetime.utcnow()

            await db.commit()
            return True

    async def delete_notification(self, id: uuid.UUID) -> bool:
        """Delete a notification."""
        from app.models.notification import Notification
        from sqlalchemy import select
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Notification).where(
                    Notification.id == id,
                    Notification.user_id == self.id,
                )
            )
            notification = result.scalar_one_or_none()

            if not notification:
                raise ValueError("Notification not found")

            await db.delete(notification)
            await db.commit()
            return True

    # Settings methods
    async def update_settings(self, input):
        """Update user settings."""
        from app.models.settings import UserSettings
        from sqlalchemy import select
        from app.db.session import get_db
        from app.graphql.types.user import UserSettings as GQLUserSettings

        async with get_db() as db:
            result = await db.execute(
                select(UserSettings).where(
                    UserSettings.user_id == self.id,
                )
            )
            settings = result.scalar_one_or_none()

            if not settings:
                settings = UserSettings(user_id=self.id)
                db.add(settings)

            update_data = {k: v for k, v in __import__('strawberry').asdict(input).items() if v is not None}
            for field, value in update_data.items():
                if value is not None:
                    setattr(settings, field, value)

            await db.commit()
            await db.refresh(settings)

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

    # Calendar convenience methods
    async def get_calendar_events(self, range):
        """Get events for calendar view."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Event)
                .where(
                    Event.user_id == self.id,
                    Event.deleted_at.is_(None),
                    Event.status == EventStatus.SCHEDULED,
                    Event.start_time < range.end_date,
                    Event.end_time > range.start_date,
                )
                .options(
                    selectinload(Event.category),
                    selectinload(Event.reminders),
                )
                .order_by(Event.start_time)
            )
            events = result.scalars().all()
            return events

    async def get_today_events(self):
        """Get today's events."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db
        from datetime import timedelta

        async with get_db() as db:
            now = datetime.utcnow()
            start = datetime(now.year, now.month, now.day)
            end = start + timedelta(days=1)

            result = await db.execute(
                select(Event)
                .where(
                    Event.user_id == self.id,
                    Event.deleted_at.is_(None),
                    Event.status == EventStatus.SCHEDULED,
                    Event.start_time >= start,
                    Event.start_time < end,
                )
                .options(
                    selectinload(Event.category),
                    selectinload(Event.reminders),
                )
                .order_by(Event.start_time)
            )
            events = result.scalars().all()
            return events

    async def get_this_week_events(self):
        """Get this week's events."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db
        from datetime import timedelta

        async with get_db() as db:
            now = datetime.utcnow()
            week_start = now - timedelta(days=now.weekday())
            week_end = week_start + timedelta(days=7)

            result = await db.execute(
                select(Event)
                .where(
                    Event.user_id == self.id,
                    Event.deleted_at.is_(None),
                    Event.status == EventStatus.SCHEDULED,
                    Event.start_time >= week_start,
                    Event.start_time < week_end,
                )
                .options(
                    selectinload(Event.category),
                    selectinload(Event.reminders),
                )
                .order_by(Event.start_time)
            )
            events = result.scalars().all()
            return events

    async def get_this_month_events(self):
        """Get this month's events."""
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import get_db

        async with get_db() as db:
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            if now.month == 12:
                month_end = datetime(now.year + 1, 1, 1)
            else:
                month_end = datetime(now.year, now.month + 1, 1)

            result = await db.execute(
                select(Event)
                .where(
                    Event.user_id == self.id,
                    Event.deleted_at.is_(None),
                    Event.status == EventStatus.SCHEDULED,
                    Event.start_time >= month_start,
                    Event.start_time < month_end,
                )
                .options(
                    selectinload(Event.category),
                    selectinload(Event.reminders),
                )
                .order_by(Event.start_time)
            )
            events = result.scalars().all()
            return events

    # AI Planner methods
    async def propose_events(self, conversation_id: uuid.UUID, proposal):
        """Propose events from AI planner."""
        from app.models.conversation import Conversation
        from app.models.event import Event, EventPriority
        from sqlalchemy import select
        from app.db.session import get_db
        from app.graphql.types.event import ProposedEvent

        async with get_db() as db:
            # Verify conversation belongs to user
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == self.id,
                )
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ValueError("Conversation not found")

            # Create proposed events
            proposed = []
            for event_input in proposal.events:
                proposed_event = ProposedEvent(
                    id=uuid.uuid4(),
                    title=event_input.title,
                    description=event_input.description,
                    suggested_start_time=event_input.suggested_start_time,
                    suggested_end_time=event_input.suggested_end_time,
                    category=event_input.category,
                    priority=event_input.priority,
                    preparation_notes=event_input.preparation_notes,
                    reminders=event_input.reminders,
                )
                proposed.append(proposed_event)

            return proposed

    async def confirm_proposed_events(self, conversation_id: uuid.UUID, event_ids: list[uuid.UUID]):
        """Confirm proposed events."""
        from app.models.conversation import Conversation
        from app.models.event import Event, EventStatus
        from sqlalchemy import select
        from app.db.session import get_db

        async with get_db() as db:
            # Verify conversation belongs to user
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == self.id,
                )
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ValueError("Conversation not found")

            # Create confirmed events
            events = []
            for event_id in event_ids:
                # In a real implementation, this would get the proposed event from the conversation
                # and create a confirmed event
                pass

            return events

    async def reject_proposed_events(self, conversation_id: uuid.UUID, event_ids: list[uuid.UUID]) -> bool:
        """Reject proposed events."""
        from app.models.conversation import Conversation
        from sqlalchemy import select
        from app.db.session import get_db

        async with get_db() as db:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == self.id,
                )
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise ValueError("Conversation not found")

            return True
