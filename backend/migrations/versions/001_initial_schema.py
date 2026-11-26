"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-11-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Create enum types with uppercase values
    op.execute("CREATE TYPE theme AS ENUM ('LIGHT', 'DARK', 'SYSTEM')")
    op.execute("CREATE TYPE calendarview AS ENUM ('MONTH', 'WEEK', 'DAY', 'YEAR', 'UPCOMING', 'PAST')")
    op.execute("CREATE TYPE eventpriority AS ENUM ('NORMAL', 'HIGH', 'CRITICAL')")
    op.execute("CREATE TYPE eventstatus AS ENUM ('SCHEDULED', 'COMPLETED', 'CANCELLED')")
    op.execute("CREATE TYPE notificationtype AS ENUM ('IN_APP', 'EMAIL', 'PUSH')")
    op.execute("CREATE TYPE conversationrole AS ENUM ('USER', 'ASSISTANT', 'SYSTEM', 'TOOL')")
    op.execute("CREATE TYPE memorytype AS ENUM ('GOAL', 'PREFERENCE', 'COMMITMENT', 'FACT', 'SUMMARY')")
    op.execute("CREATE TYPE notificationcategory AS ENUM ('REMINDER', 'EVENT_CREATED', 'EVENT_UPDATED', 'EVENT_DELETED', 'AI_SUGGESTION', 'SYSTEM')")

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('timezone', sa.String(50), server_default='UTC', nullable=False),
        sa.Column('locale', sa.String(10), server_default='en', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_active', 'users', ['is_active'], postgresql_where=sa.text('is_active = true'))

    # Categories table
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=False),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('default_reminder_minutes', postgresql.ARRAY(sa.Integer()), server_default='{1440,60,15}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_categories_user', 'categories', ['user_id'])
    op.create_index('ix_categories_parent', 'categories', ['parent_id'])
    op.create_index('ix_categories_user_name_unique', 'categories', ['user_id', 'name'], unique=True, postgresql_where=sa.text('deleted_at IS NULL'))

    # Events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(500), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('all_day', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('timezone', sa.String(50), server_default='UTC', nullable=False),
        sa.Column('priority', sa.Enum('NORMAL', 'HIGH', 'CRITICAL', name='eventpriority', create_type=False), server_default='NORMAL', nullable=False),
        sa.Column('status', sa.Enum('SCHEDULED', 'COMPLETED', 'CANCELLED', name='eventstatus', create_type=False), server_default='SCHEDULED', nullable=False),
        sa.Column('is_recurring', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('rrule', sa.Text(), nullable=True),
        sa.Column('rrule_original_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recurrence_exceptions', postgresql.ARRAY(sa.DateTime(timezone=True)), server_default=sa.text("'{}'::timestamptz[]"), nullable=False),
        sa.Column('preparation_notes', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_events_user', 'events', ['user_id'])
    op.create_index('ix_events_category', 'events', ['category_id'])
    op.create_index('ix_events_start_time', 'events', ['start_time'])
    op.create_index('ix_events_date_range', 'events', ['user_id', 'start_time', 'end_time'])
    op.create_index('ix_events_recurring', 'events', ['is_recurring'], postgresql_where=sa.text('is_recurring = true'))
    op.create_index('ix_events_status', 'events', ['status'])

    # Event Reminders table
    op.create_table(
        'event_reminders',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('minutes_before', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.Enum('IN_APP', 'EMAIL', 'PUSH', name='notificationtype', create_type=False), server_default='IN_APP', nullable=False),
        sa.Column('is_sent', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reminders_event', 'event_reminders', ['event_id'])
    op.create_index('ix_reminders_user_pending', 'event_reminders', ['user_id', 'is_sent'], postgresql_where=sa.text('is_sent = false'))
    op.create_index('ix_reminders_scheduled', 'event_reminders', ['minutes_before'], postgresql_where=sa.text('is_sent = false'))

    # Conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('model_provider', sa.String(50), server_default='openai', nullable=False),
        sa.Column('model_name', sa.String(100), server_default='gpt-4o', nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_conversations_user', 'conversations', ['user_id'])

    # Messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('USER', 'ASSISTANT', 'SYSTEM', 'TOOL', name='conversationrole', create_type=False), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tool_calls', postgresql.JSONB(), nullable=True),
        sa.Column('tool_call_id', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_messages_conversation', 'messages', ['conversation_id'])
    op.create_index('ix_messages_created', 'messages', ['created_at'])

    # User Memory table
    op.create_table(
        'user_memory',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('memory_type', sa.Enum('GOAL', 'PREFERENCE', 'COMMITMENT', 'FACT', 'SUMMARY', name='memorytype', create_type=False), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.ARRAY(sa.Float()), nullable=True),
        sa.Column('source_conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_conversation_id'], ['conversations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_memory_user', 'user_memory', ['user_id'])
    op.create_index('ix_memory_type', 'user_memory', ['memory_type'])
    op.create_index('ix_memory_active', 'user_memory', ['is_active'], postgresql_where=sa.text('is_active = true'))

    # Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('REMINDER', 'EVENT_CREATED', 'EVENT_UPDATED', 'EVENT_DELETED', 'AI_SUGGESTION', 'SYSTEM', name='notificationcategory', create_type=False), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_user', 'notifications', ['user_id'])
    op.create_index('ix_notifications_unread', 'notifications', ['user_id', 'is_read'], postgresql_where=sa.text('is_read = false'))
    op.create_index('ix_notifications_created', 'notifications', ['created_at'])

    # User Settings table
    op.create_table(
        'user_settings',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('theme', sa.Enum('LIGHT', 'DARK', 'SYSTEM', name='theme', create_type=False), server_default='SYSTEM', nullable=False),
        sa.Column('calendar_default_view', sa.Enum('MONTH', 'WEEK', 'DAY', 'YEAR', 'UPCOMING', 'PAST', name='calendarview', create_type=False), server_default='MONTH', nullable=False),
        sa.Column('week_start_day', sa.Integer(), server_default='0', nullable=False),
        sa.Column('default_reminder_minutes', postgresql.ARRAY(sa.Integer()), server_default='{1440,60,15}', nullable=False),
        sa.Column('notification_email', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('notification_push', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ai_provider', sa.String(50), server_default='openai', nullable=False),
        sa.Column('ai_model', sa.String(100), server_default='gpt-4o', nullable=False),
        sa.Column('language', sa.String(10), server_default='en', nullable=False),
        sa.Column('date_format', sa.String(20), server_default='YYYY-MM-DD', nullable=False),
        sa.Column('time_format', sa.String(10), server_default='24h', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
    )

    # Create function to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Create triggers for updated_at
    tables_with_updated_at = [
        'users', 'categories', 'events', 'conversations',
        'user_memory', 'notifications', 'user_settings'
    ]
    for table in tables_with_updated_at:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers
    tables_with_updated_at = [
        'users', 'categories', 'events', 'conversations',
        'user_memory', 'notifications', 'user_settings'
    ]
    for table in tables_with_updated_at:
        op.execute(f'DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}')

    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')

    # Drop tables in reverse order
    op.drop_table('user_settings')
    op.drop_table('notifications')
    op.drop_table('user_memory')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('event_reminders')
    op.drop_table('events')
    op.drop_table('categories')
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS eventpriority')
    op.execute('DROP TYPE IF EXISTS eventstatus')
    op.execute('DROP TYPE IF EXISTS notificationtype')
    op.execute('DROP TYPE IF EXISTS conversationrole')
    op.execute('DROP TYPE IF EXISTS memorytype')
    op.execute('DROP TYPE IF EXISTS notificationcategory')
    op.execute('DROP TYPE IF EXISTS theme')
    op.execute('DROP TYPE IF EXISTS calendarview')
    op.execute('DROP TYPE IF EXISTS eventstatus')
    op.execute('DROP TYPE IF EXISTS notificationtype')
    op.execute('DROP TYPE IF EXISTS conversationrole')
    op.execute('DROP TYPE IF EXISTS memorytype')
    op.execute('DROP TYPE IF EXISTS notificationcategory')
    op.execute('DROP TYPE IF EXISTS theme')
    op.execute('DROP TYPE IF EXISTS calendarview')