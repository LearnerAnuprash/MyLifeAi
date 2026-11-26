"""Notification service."""
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationCategory
from app.graphql.types.notification import Notification as GQLNotification, NotificationConnection, NotificationEdge
from app.graphql.types.event import PageInfo
from app.graphql.serializers import notification_to_gql


class NotificationService:
    """Notification service for in-app notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_notifications(
        self,
        user_id: uuid.UUID,
        filter: Optional["NotificationFilterInput"] = None,
        first: int = 20,
        after: Optional[str] = None,
    ) -> NotificationConnection:
        """Get user's notifications with pagination."""
        from app.graphql.types.inputs import NotificationFilterInput

        query = select(Notification).where(
            Notification.user_id == user_id,
        ).order_by(Notification.created_at.desc())

        if filter:
            if filter.is_read is not None:
                query = query.where(Notification.is_read == filter.is_read)
            if filter.types:
                query = query.where(Notification.type.in_(filter.types))

        if after:
            try:
                after_id = uuid.UUID(after)
                result = await self.db.execute(
                    select(Notification.created_at).where(Notification.id == after_id)
                )
                after_time = result.scalar_one_or_none()
                if after_time:
                    query = query.where(Notification.created_at < after_time)
            except ValueError:
                pass

        query = query.limit(first + 1)
        result = await self.db.execute(query)
        notifications = result.scalars().all()

        has_next_page = len(notifications) > first
        if has_next_page:
            notifications = notifications[:first]

        gql_notifications = [notification_to_gql(n) for n in notifications]

        edges = [
            NotificationEdge(node=notif, cursor=str(notif.id))
            for notif in gql_notifications
        ]

        # Total count
        count_query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
        )
        if filter:
            if filter.is_read is not None:
                count_query = count_query.where(Notification.is_read == filter.is_read)
            if filter.types:
                count_query = count_query.where(Notification.type.in_(filter.types))
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Unread count
        unread_query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        unread_result = await self.db.execute(unread_query)
        unread_count = unread_result.scalar() or 0

        page_info = PageInfo(
            has_next_page=has_next_page,
            has_previous_page=after is not None,
            start_cursor=str(edges[0].node.id) if edges else None,
            end_cursor=str(edges[-1].node.id) if edges else None,
        )

        return NotificationConnection(
            edges=edges,
            page_info=page_info,
            total_count=total_count,
            unread_count=unread_count,
        )

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get count of unread notifications."""
        result = await self.db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        return result.scalar() or 0

    async def mark_read(self, user_id: uuid.UUID, notification_id: uuid.UUID) -> GQLNotification:
        """Mark notification as read."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise ValueError("Notification not found")

        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(notification)

        return notification_to_gql(notification)

    async def mark_all_read(self, user_id: uuid.UUID) -> bool:
        """Mark all notifications as read."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        notifications = result.scalars().all()

        for notif in notifications:
            notif.is_read = True
            notif.read_at = datetime.now(timezone.utc)

        await self.db.commit()
        return True

    async def delete_notification(
        self,
        user_id: uuid.UUID,
        notification_id: uuid.UUID,
    ) -> bool:
        """Delete a notification."""
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise ValueError("Notification not found")

        await self.db.delete(notification)
        await self.db.commit()
        return True

    async def create_notification(
        self,
        user_id: uuid.UUID,
        type: NotificationCategory,
        title: str,
        body: Optional[str] = None,
        reference_id: Optional[uuid.UUID] = None,
        reference_type: Optional[str] = None,
    ) -> GQLNotification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            reference_id=reference_id,
            reference_type=reference_type,
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        return notification_to_gql(notification)
