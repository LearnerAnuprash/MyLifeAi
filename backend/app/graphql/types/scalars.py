"""GraphQL custom scalars."""
import uuid
from datetime import datetime
from typing import Any
import strawberry


# DateTime scalar
def serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


DateTime = strawberry.scalar(
    datetime,
    serialize=serialize_datetime,
    parse_value=parse_datetime,
    description="ISO 8601 datetime string",
)


# UUID scalar
def serialize_uuid(value: uuid.UUID) -> str:
    return str(value)


def parse_uuid(value: str) -> uuid.UUID:
    return uuid.UUID(value)


UUID = strawberry.scalar(
    uuid.UUID,
    serialize=serialize_uuid,
    parse_value=parse_uuid,
    description="UUID string",
)


# JSON scalar
def serialize_json(value: Any) -> Any:
    return value


def parse_json(value: Any) -> Any:
    return value


JSON = strawberry.scalar(
    Any,
    serialize=serialize_json,
    parse_value=parse_json,
    description="JSON object",
)