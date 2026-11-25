# Changelog

All notable changes to My Life AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-24

### Added

#### Documentation
- Project architecture and design documentation
- Database schema design (PostgreSQL with UUIDs, indexes, relationships)
- GraphQL API schema specification
- Design system with color tokens, typography, spacing, components
- Implementation roadmap (6 phases)
- Agent team instructions

#### Backend (FastAPI + Strawberry GraphQL)
- Multi-stage Dockerfile for development and production
- Docker Compose with PostgreSQL, Redis, Backend, Celery Worker, Celery Beat, Frontend
- Pydantic Settings configuration management
- SQLAlchemy 2.x async models:
  - User (auth, profile, settings)
  - Category (hierarchical with system defaults)
  - Event (recurring via RRULE, reminders, timezone-aware)
  - EventReminder (configurable timing, notification types)
  - Conversation & Message (AI chat history)
  - UserMemory (personal AI context with pgvector support)
  - Notification (in-app with read status)
  - UserSettings (theme, calendar, notifications, AI, language)
- Complete GraphQL Schema:
  - Custom scalars (DateTime, UUID, JSON)
  - Enums for all domain types
  - Types, Inputs, Payloads with error handling
  - Queries (with pagination), Mutations, Subscriptions
- Domain Services:
  - AuthService (JWT, bcrypt, register/login/refresh/verify)
  - CategoryService (CRUD, tree, reorder)
  - EventService (CRUD, recurring expansion, date-range queries)
  - ConversationService (CRUD, messages)
  - MemoryService (CRUD, semantic search placeholder)
  - NotificationService (CRUD, unread count)
  - SettingsService (CRUD)
  - AIService (LLM abstraction: OpenAI, Anthropic, streaming, tools)
- GraphQL Context with request-scoped DB session and auth

#### Frontend (React 18 + TypeScript + Vite)
- Vite + TypeScript + Tailwind CSS + Ant Design setup
- Zustand stores: auth, theme, categories, notifications
- GraphQL client with auth token management
- WebSocket subscription client (foundation)
- Pages:
  - LoginPage / RegisterPage (form validation, JWT auth)
  - CalendarPage (Month/Week/Day views, event CRUD)
  - PlannerPage (Conversation list, real-time chat UI)
  - NotificationsPage (List, filter, mark read, delete)
  - SettingsPage (Tabbed: Profile, Appearance, Calendar, Notifications, AI, Language)
- Layout: Responsive sidebar, mobile drawer, user menu
- Calendar Components: Grid-based month, time-slot week/day, event chips
- Event Modal: Full form with validation, category select, reminders
- Theme System: Light/Dark/System with CSS variables, localStorage persistence
- Date Utilities: date-fns + date-fns-tz for timezone handling

### Infrastructure
- Docker Compose development environment
- PostgreSQL 16 with persistence
- Redis 7 for caching and Celery broker
- Celery worker for background tasks
- Celery beat for scheduled tasks
- Nginx-ready production configuration

### Security
- JWT authentication with access/refresh tokens
- Bcrypt password hashing
- CORS configuration
- Input validation via Pydantic/Zod
- SQL injection prevention via SQLAlchemy ORM

## [Unreleased]

### Planned
- Alembic database migrations
- GraphQL Codegen TypeScript types
- Recurring event RRULE editor UI
- Category management UI in settings
- Celery reminder scheduling tasks
- AI planner tool execution backend
- WebSocket real-time subscriptions
- Automated test suite
- Production Docker configuration
- Deployment documentation