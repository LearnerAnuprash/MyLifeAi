# Database Schema Design - My Life AI

## Overview
PostgreSQL database with UUID primary keys, proper foreign keys, constraints, and timezone-aware timestamps.

## Tables

### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'UTC',
    locale VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active;
```

### categories
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(7) NOT NULL, -- Hex color #RRGGBB
    icon VARCHAR(50), -- Icon identifier
    is_system BOOLEAN DEFAULT false, -- System categories cannot be deleted
    sort_order INTEGER DEFAULT 0,
    default_reminder_minutes INTEGER[], -- Array of reminder offsets
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_categories_user ON categories(user_id);
CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE UNIQUE INDEX idx_categories_user_name ON categories(user_id, name) WHERE deleted_at IS NULL;
```

### events
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(500),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    all_day BOOLEAN DEFAULT false,
    timezone VARCHAR(50) NOT NULL, -- IANA timezone for display
    priority INTEGER DEFAULT 0, -- 0=normal, 1=high, 2=critical
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, completed, cancelled
    is_recurring BOOLEAN DEFAULT false,
    rrule TEXT, -- RFC 5545 RRULE string
    rrule_original_start TIMESTAMPTZ, -- Original start for recurring instances
    recurrence_exceptions TIMESTAMPTZ[] DEFAULT ARRAY[]::TIMESTAMPTZ[], -- Skipped occurrence timestamps
    preparation_notes TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_category ON events(category_id);
CREATE INDEX idx_events_start_time ON events(start_time);
CREATE INDEX idx_events_date_range ON events(user_id, start_time, end_time);
CREATE INDEX idx_events_recurring ON events(is_recurring) WHERE is_recurring;
CREATE INDEX idx_events_status ON events(status);
```

### event_reminders
```sql
CREATE TABLE event_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    minutes_before INTEGER NOT NULL, -- Negative for after event start
    notification_type VARCHAR(20) DEFAULT 'in_app', -- in_app, email, push
    is_sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reminders_event ON event_reminders(event_id);
CREATE INDEX idx_reminders_user_time ON event_reminders(user_id, is_sent) WHERE NOT is_sent;
CREATE INDEX idx_reminders_scheduled ON event_reminders(minutes_before) WHERE NOT is_sent;
```

### conversations
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    model_provider VARCHAR(50),
    model_name VARCHAR(100),
    system_prompt TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
```

### messages
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user, assistant, system, tool
    content TEXT NOT NULL,
    tool_calls JSONB, -- For assistant tool calls
    tool_call_id VARCHAR(100), -- For tool responses
    metadata JSONB, -- Token usage, model info, etc.
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(created_at);
```

### user_memory
```sql
CREATE TABLE user_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL, -- goal, preference, commitment, fact, summary
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- pgvector for semantic search
    source_conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    confidence FLOAT DEFAULT 1.0, -- 0.0 to 1.0
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_memory_user ON user_memory(user_id);
CREATE INDEX idx_memory_type ON user_memory(memory_type);
CREATE INDEX idx_memory_active ON user_memory(is_active) WHERE is_active;
-- Vector index created separately: CREATE INDEX ON user_memory USING ivfflat (embedding vector_cosine_ops);
```

### notifications
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- reminder, event_created, event_updated, ai_suggestion, etc.
    title VARCHAR(255) NOT NULL,
    body TEXT,
    reference_id UUID, -- Event ID, conversation ID, etc.
    reference_type VARCHAR(50),
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE NOT is_read;
CREATE INDEX idx_notifications_created ON notifications(created_at);
```

### user_settings
```sql
CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'system', -- light, dark, system
    calendar_default_view VARCHAR(20) DEFAULT 'month', -- month, week, day, year
    week_start_day INTEGER DEFAULT 0, -- 0=Sunday, 1=Monday
    default_reminder_minutes INTEGER[] DEFAULT '{1440, 60, 15}', -- 1 day, 1 hour, 15 min
    notification_email BOOLEAN DEFAULT false,
    notification_push BOOLEAN DEFAULT false,
    ai_provider VARCHAR(50) DEFAULT 'openai',
    ai_model VARCHAR(100) DEFAULT 'gpt-4o',
    language VARCHAR(10) DEFAULT 'en',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    time_format VARCHAR(10) DEFAULT '24h',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Default Categories (System)

Inserted on user creation:

1. **FAMILY** (#E91E63) - Birthdays, Anniversaries, Family gatherings, Check on someone, Stay connected, Family trips, Important family dates
2. **CAREER** (#2196F3) - IT events, Tech expos, Hackathons, Conferences, Networking, Interviews, Job applications, Professional development
3. **ENTERTAINMENT** (#9C27B0) - Concerts, Movie releases, Sports, Festivals, Personal outings, Entertainment plans
4. **IMPORTANT REMINDERS** (#FF5722) - Subscriptions, Documents, Bills, Deadlines, Follow-ups, Announcements
5. **PERSONAL** (#4CAF50) - Goals, Routines, Appointments, Fitness, Learning, Milestones

## Recurring Events Strategy

Using RFC 5545 RRULE standard with these considerations:
- Store RRULE as text in `events.rrule`
- Original recurring event has `is_recurring=true`
- Exceptions stored as separate events with `rrule_original_start` pointing to original
- `recurrence_exceptions` array on master event tracks skipped occurrence timestamps (UTC)
- Backend expands recurring events for calendar queries (up to 2 years ahead)

## Timezone Handling

- All timestamps stored in UTC (TIMESTAMPTZ)
- User's preferred timezone in `users.timezone`
- Event-specific timezone in `events.timezone` for display
- Frontend converts UTC to user/event timezone for display
- Recurring events evaluated in event's timezone

## Indexes for Performance

Key composite indexes for common queries:
- `events(user_id, start_time, end_time)` - Calendar range queries
- `event_reminders(user_id, is_sent)` - Pending reminders
- `notifications(user_id, is_read)` - Unread notifications
- `messages(conversation_id, created_at)` - Conversation history

## Migrations

Managed via Alembic with:
- One migration per logical change
- Reversible migrations where possible
- Data migrations for schema changes