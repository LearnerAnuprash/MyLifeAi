# AGENTS.md - My Life AI Engineering Team Instructions

This file defines the engineering team structure and conventions for the My Life AI project.

## Agent Responsibilities

### Lead Architect
- Maintain overall architecture
- Define implementation milestones
- Review technical decisions
- Prevent redundant work
- Coordinate between agents
- Update ROADMAP.md and WORKLOG.md

### Frontend Engineer
- Design system and component library
- Calendar interface implementation (Month/Week/Day/Year views)
- Event management UI (CRUD, modals, forms)
- Planner interface (chat, conversations)
- GraphQL integration (queries, mutations, subscriptions)
- Responsive implementation (mobile, tablet, desktop)
- Theme system (light/dark/system)
- Accessibility (WCAG AA)

### Backend Engineer
- Database architecture and migrations (Alembic)
- GraphQL schema design (Strawberry)
- Domain services (Auth, Category, Event, Conversation, Memory, Notification, Settings, AI)
- Authentication and authorization (JWT, bcrypt)
- Event and reminder systems (recurring, timezone handling)
- Background processing (Celery tasks for reminders, notifications, maintenance)
- API documentation and health checks

### AI Engineer
- LLM provider abstraction (OpenAI, Anthropic, extensible)
- AI planner implementation (conversational, tool calling)
- Tool calling architecture (calendar, memory, categories)
- Personal memory system (pgvector semantic search)
- Context retrieval (relevant memories, conversations)
- Streaming responses

### QA Engineer
- Test critical user journeys
- Identify regressions
- Validate frontend/backend integration
- Check authorization (user data isolation)
- Test timezone and recurring-event behavior
- Automated test coverage

## Coordination Protocol

1. **No simultaneous file modifications** - Agents must coordinate through shared documentation
2. **Document decisions** - All architectural decisions go in `/docs/decisions/`
3. **Update worklog** - Update WORKLOG.md after meaningful milestones
4. **Verify before proceeding** - Never claim implementation complete without verification
5. **Use Git branches** - Feature branches for all changes, PRs required

## Git Conventions

- Branch naming: `feature/<area>-<description>`, `fix/<area>-<description>`, `refactor/<area>-<description>`
- Commit messages: Conventional commits format (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`)
- PR required for all changes to main branch

## Code Standards

### TypeScript (Frontend)
- Strict mode enabled
- No `any` types unless justified with `// @ts-expect-error` comment
- Reusable components in `/src/components/ui/`
- Feature-based folder structure
- Centralized GraphQL operations in `/src/graphql/`
- Zod validation for all forms
- React Hook Form for form handling
- TanStack Query for server state
- Zustand for client state

### Python (Backend)
- Type hints required everywhere
- MyPy strict mode
- Pydantic models for validation
- SQLAlchemy 2.x async patterns
- Centralized exception handling
- Structured logging with structlog
- Ruff for linting/formatting

### GraphQL
- Schema-first with Strawberry
- Code generation for frontend types
- Relay-style cursor pagination
- Proper error handling with unions
- Subscriptions for real-time updates

### Database
- UUID primary keys
- Proper foreign keys and constraints
- Indexes for query performance
- Timezone-aware timestamps (UTC storage)
- Soft deletes where justified
- pgvector for semantic search

## Development Workflow

### Starting a New Task
1. Read AGENTS.md, ROADMAP.md, WORKLOG.md
2. Check current repository state
3. Identify unfinished tasks
4. Create feature branch
5. Implement with tests
6. Update documentation
7. Create PR

### Testing Requirements
- Unit tests for business logic (pytest, vitest)
- Integration tests for API endpoints
- E2E tests for critical user flows (Playwright)
- Run tests before PR

### Documentation Updates
- Update WORKLOG.md after each milestone
- Update CHANGELOG.md for releases
- Document API changes in `/docs/api/`
- Document schema changes in `/docs/database/`

## Current Project State

### Completed (Phase 0 & 1)
- ✅ Project structure and documentation
- ✅ Database schema design
- ✅ GraphQL schema design
- ✅ Design system documentation
- ✅ Docker Compose development environment
- ✅ FastAPI backend with Strawberry GraphQL
- ✅ SQLAlchemy models (User, Category, Event, Conversation, Message, UserMemory, Notification, UserSettings)
- ✅ Domain services (Auth, Category, Event, Conversation, Memory, Notification, Settings, AI)
- ✅ React frontend with Vite, TypeScript, Tailwind, Ant Design
- ✅ Zustand stores (auth, theme, categories, notifications)
- ✅ GraphQL client with auth token management
- ✅ Pages: Login, Register, Calendar, Planner, Notifications, Settings
- ✅ Calendar components (Month/Week/Day views)
- ✅ Event modal (create/edit)
- ✅ Theme system (light/dark/system)
- ✅ Alembic migration (initial schema)
- ✅ Celery worker configuration with tasks
- ✅ Production deployment documentation

### In Progress / Next Steps (Phase 2)
- [ ] Test Docker Compose startup
- [ ] Run database migrations
- [ ] Generate GraphQL TypeScript types
- [ ] Integration testing (frontend ↔ backend)
- [ ] Recurring event RRULE editor UI
- [ ] Category management UI in settings
- [ ] Reminder system Celery task testing
- [ ] AI planner tool execution backend
- [ ] WebSocket subscriptions

### Phase 3 (Reminders)
- [ ] In-app notification real-time updates
- [ ] Email notification integration
- [ ] Push notification preparation

### Phase 4 (AI Planner)
- [ ] LLM provider integration (OpenAI/Anthropic keys)
- [ ] Tool calling execution
- [ ] Structured event proposals
- [ ] User confirmation flow

### Phase 5 (Personal Intelligence)
- [ ] pgvector setup for embeddings
- [ ] Semantic memory search
- [ ] Weekly summaries
- [ ] Goal tracking

### Phase 6 (Production Readiness)
- [ ] Automated test suite
- [ ] Security review
- [ ] Performance optimization
- [ ] Production Docker config
- [ ] Monitoring and alerting
- [ ] Backup strategy

## Key Files Reference

### Backend
- `backend/app/main.py` - FastAPI app entry point
- `backend/app/graphql/schema.py` - GraphQL schema
- `backend/app/db/session.py` - Database session
- `backend/app/models/` - SQLAlchemy models
- `backend/app/services/` - Domain services
- `backend/app/workers/` - Celery tasks
- `backend/migrations/` - Alembic migrations

### Frontend
- `frontend/src/main.tsx` - App entry point
- `frontend/src/App.tsx` - Routing
- `frontend/src/pages/` - Page components
- `frontend/src/components/` - Reusable components
- `frontend/src/store/` - Zustand stores
- `frontend/src/utils/graphqlClient.ts` - GraphQL client
- `frontend/src/styles/globals.css` - Design tokens

### Documentation
- `ROADMAP.md` - Implementation phases
- `WORKLOG.md` - Development log
- `CHANGELOG.md` - Version history
- `docs/architecture/design-system.md` - Design tokens
- `docs/database/schema.md` - Database schema
- `docs/api/graphql-schema.md` - GraphQL schema
- `docs/deployment/development.md` - Dev setup
- `docs/deployment/production.md` - Prod deployment