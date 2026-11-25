# My Life AI

An intelligent personal life management platform combining a visually exceptional calendar, AI-powered planning, and personal memory system.

## Vision

Build a platform that helps people:
- Remember important dates and never miss commitments
- Organize their lives with intelligent categorization
- Discover opportunities through AI-powered suggestions
- Plan their future with an AI brainstorming partner
- Maintain long-term personal organization

## Tech Stack

### Frontend
- React 18 + TypeScript + Vite
- Ant Design + Tailwind CSS
- Zustand (state management)
- GraphQL + GraphQL Code Generator
- React Router + TanStack Query
- React Hook Form + Zod

### Backend
- Python 3.11+ + FastAPI
- Strawberry GraphQL
- SQLAlchemy 2.x + Alembic
- PostgreSQL (asyncpg)
- Redis + Celery

### Infrastructure
- Docker + Docker Compose
- PostgreSQL + Redis containers
- Nginx (production)

## Project Structure

```
my-life/
├── frontend/           # React application
├── backend/            # FastAPI application
├── docs/               # Documentation
│   ├── architecture/   # Architecture decisions
│   ├── database/       # Schema documentation
│   ├── api/           # API documentation
│   ├── deployment/    # Deployment guides
│   ├── decisions/     # ADRs
│   └── features/      # Feature specs
├── AGENTS.md          # Team instructions
├── ROADMAP.md         # Implementation roadmap
├── WORKLOG.md         # Progress tracking
└── CHANGELOG.md       # Version history
```

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Quick Start (Docker)

```bash
docker compose up -d --build
```

### Development

```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend
cd backend && pip install -e . && uvicorn app.main:app --reload
```

## Documentation

- [Architecture](/docs/architecture)
- [Database Schema](/docs/database)
- [API Reference](/docs/api)
- [Deployment Guide](/docs/deployment)
- [Decisions Log](/docs/decisions)
- [Feature Specs](/docs/features)

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the implementation phases.

## License

MIT