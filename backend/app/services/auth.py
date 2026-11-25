"""Authentication service."""
from datetime import datetime, timedelta
from typing import Optional
import uuid
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.settings import UserSettings
from app.core.config import get_settings
from app.graphql.types.inputs import RegisterInput, LoginInput
from app.graphql.types.payloads import AuthPayload
from app.graphql.types.user import User as GQLUser, UserSettings as GQLUserSettings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user_id: uuid.UUID) -> str:
        """Create JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": str(user_id), "exp": expire, "type": "access"}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def create_refresh_token(self, user_id: uuid.UUID) -> str:
        """Create JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {"sub": str(user_id), "exp": expire, "type": "refresh"}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None

    async def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from access token."""
        payload = self.decode_token(token)
        if not payload or payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id), User.is_active == True, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def register(self, input: RegisterInput) -> AuthPayload:
        """Register a new user."""
        # Check if email exists
        result = await self.db.execute(
            select(User).where(User.email == input.email, User.deleted_at.is_(None))
        )
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")

        # Validate password strength
        if len(input.password) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")

        # Create user
        user = User(
            email=input.email,
            password_hash=self.hash_password(input.password),
            full_name=input.full_name,
        )
        self.db.add(user)
        await self.db.flush()

        # Create default settings
        user_settings = UserSettings(user_id=user.id)
        self.db.add(user_settings)

        # Create default system categories
        await self._create_default_categories(user.id)

        await self.db.commit()
        await self.db.refresh(user)

        # Generate tokens
        access_token = self.create_access_token(user.id)
        refresh_token = self.create_refresh_token(user.id)

        return AuthPayload(
            token=access_token,
            user=await self._user_to_gql(user),
        )

    async def login(self, input: LoginInput) -> AuthPayload:
        """Authenticate user and return tokens."""
        result = await self.db.execute(
            select(User).where(User.email == input.email, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()

        if not user or not self.verify_password(input.password, user.password_hash):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        # Generate tokens
        access_token = self.create_access_token(user.id)
        refresh_token = self.create_refresh_token(user.id)

        return AuthPayload(
            token=access_token,
            user=await self._user_to_gql(user),
        )

    async def refresh_token(self, refresh_token: Optional[str]) -> str:
        """Refresh access token using refresh token."""
        if not refresh_token:
            raise ValueError("Refresh token required")

        payload = self.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid refresh token")

        # Verify user still exists and is active
        result = await self.db.execute(
            select(User).where(User.id == uuid.UUID(user_id), User.is_active == True, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found or inactive")

        return self.create_access_token(user.id)

    async def verify_email(self, token: str) -> bool:
        """Verify user's email address."""
        # Implementation would decode verification token and update user
        # For now, placeholder
        return True

    async def request_password_reset(self, email: str) -> bool:
        """Request password reset email."""
        # Implementation would send reset email
        # For now, placeholder
        return True

    async def reset_password(self, token: str, password: str) -> bool:
        """Reset password with token."""
        # Implementation would decode token and update password
        # For now, placeholder
        return True

    async def _create_default_categories(self, user_id: uuid.UUID) -> None:
        """Create default system categories for new user."""
        from app.models.category import Category

        default_categories = [
            {
                "name": "FAMILY",
                "description": "Family events and reminders",
                "color": "#E91E63",
                "icon": "heart",
                "subcategories": [
                    {"name": "Birthdays", "description": "Family birthdays"},
                    {"name": "Anniversaries", "description": "Family anniversaries"},
                    {"name": "Family Gatherings", "description": "Family events and reunions"},
                    {"name": "Check on Someone", "description": "Reminders to check on family members"},
                    {"name": "Stay Connected", "description": "Regular check-in reminders"},
                    {"name": "Family Trips", "description": "Family travel plans"},
                    {"name": "Important Family Dates", "description": "Other important family dates"},
                ],
            },
            {
                "name": "CAREER",
                "description": "Career and professional events",
                "color": "#2196F3",
                "icon": "briefcase",
                "subcategories": [
                    {"name": "IT Events", "description": "Technology events and meetups"},
                    {"name": "Tech Expos", "description": "Technology exhibitions"},
                    {"name": "Hackathons", "description": "Coding competitions"},
                    {"name": "Conferences", "description": "Professional conferences"},
                    {"name": "Networking Events", "description": "Professional networking"},
                    {"name": "Interviews", "description": "Job interviews"},
                    {"name": "Job Application Deadlines", "description": "Application deadlines"},
                    {"name": "Professional Development", "description": "Learning and growth"},
                ],
            },
            {
                "name": "ENTERTAINMENT",
                "description": "Entertainment and leisure",
                "color": "#9C27B0",
                "icon": "music",
                "subcategories": [
                    {"name": "Concerts", "description": "Live music events"},
                    {"name": "Movie Releases", "description": "New movie releases"},
                    {"name": "Movie Schedules", "description": "Planned movie viewings"},
                    {"name": "Sports Events", "description": "Sports games and matches"},
                    {"name": "Festivals", "description": "Cultural and music festivals"},
                    {"name": "Personal Outings", "description": "Personal entertainment plans"},
                    {"name": "Entertainment Plans", "description": "Other entertainment"},
                ],
            },
            {
                "name": "IMPORTANT REMINDERS",
                "description": "Critical reminders and deadlines",
                "color": "#FF5722",
                "icon": "alert-triangle",
                "subcategories": [
                    {"name": "Subscription Renewals", "description": "Service subscription renewals"},
                    {"name": "Document Expiration", "description": "Passport, license, ID expirations"},
                    {"name": "Bill Payments", "description": "Recurring bill payments"},
                    {"name": "Application Deadlines", "description": "Important application deadlines"},
                    {"name": "Follow-ups", "description": "Important follow-up reminders"},
                    {"name": "Important Announcements", "description": "Key announcements to track"},
                    {"name": "Other Time-Sensitive", "description": "Other urgent reminders"},
                ],
            },
            {
                "name": "PERSONAL",
                "description": "Personal goals and activities",
                "color": "#4CAF50",
                "icon": "user",
                "subcategories": [
                    {"name": "Personal Goals", "description": "Long-term personal goals"},
                    {"name": "Daily Routines", "description": "Recurring daily activities"},
                    {"name": "Appointments", "description": "Personal appointments"},
                    {"name": "Fitness Activities", "description": "Exercise and fitness"},
                    {"name": "Learning Schedules", "description": "Study and learning time"},
                    {"name": "Personal Milestones", "description": "Personal achievements"},
                ],
            },
        ]

        for i, cat_data in enumerate(default_categories):
            parent = Category(
                user_id=user_id,
                name=cat_data["name"],
                description=cat_data["description"],
                color=cat_data["color"],
                icon=cat_data["icon"],
                is_system=True,
                sort_order=i,
            )
            self.db.add(parent)
            await self.db.flush()

            for j, sub_data in enumerate(cat_data["subcategories"]):
                sub = Category(
                    user_id=user_id,
                    parent_id=parent.id,
                    name=sub_data["name"],
                    description=sub_data["description"],
                    color=cat_data["color"],
                    is_system=True,
                    sort_order=j,
                )
                self.db.add(sub)

    async def _user_to_gql(self, user: User) -> GQLUser:
        """Convert User model to GraphQL type."""
        # Load settings
        from sqlalchemy import select
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == user.id)
        )
        settings_obj = result.scalar_one_or_none()

        gql_settings = GQLUserSettings(
            theme=settings_obj.theme if settings_obj else "system",
            calendar_default_view=settings_obj.calendar_default_view if settings_obj else "month",
            week_start_day=settings_obj.week_start_day if settings_obj else 0,
            default_reminder_minutes=settings_obj.default_reminder_minutes if settings_obj else [1440, 60, 15],
            notification_email=settings_obj.notification_email if settings_obj else False,
            notification_push=settings_obj.notification_push if settings_obj else False,
            ai_provider=settings_obj.ai_provider if settings_obj else "openai",
            ai_model=settings_obj.ai_model if settings_obj else "gpt-4o",
            language=settings_obj.language if settings_obj else "en",
            date_format=settings_obj.date_format if settings_obj else "YYYY-MM-DD",
            time_format=settings_obj.time_format if settings_obj else "24h",
        )

        return GQLUser(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            timezone=user.timezone,
            locale=user.locale,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            settings=gql_settings,
        )