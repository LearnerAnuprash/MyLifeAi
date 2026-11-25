# Development Environment Setup

## Prerequisites

- Docker Desktop / Docker Engine + Docker Compose v2
- Git
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

## Quick Start with Docker Compose

```bash
# Clone the repository
git clone git@github.com:LearnerAnuprash/MyLifeAi.git
cd MyLifeAi

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Start all services
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 5173 | Vite dev server with HMR |
| Backend | 8000 | FastAPI + GraphQL (Playground at /graphql) |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & Celery broker |
| Celery Worker | - | Background task processing |
| Celery Beat | - | Scheduled tasks |

## Local Development (Without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"

# Copy and edit environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy and edit environment
cp .env.example .env

# Start development server
npm run dev
```

### Celery Workers

```bash
cd backend
source .venv/bin/activate

# Start worker
celery -A app.workers.celery_app worker --loglevel=info --concurrency=4

# Start beat scheduler (in another terminal)
celery -A app.workers.celery_app beat --loglevel=info
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## GraphQL Codegen (Frontend)

```bash
cd frontend

# Generate TypeScript types from GraphQL schema
npm run graphql:generate

# Or with backend running
npx graphql-codegen --config codegen.ts
```

## Useful Commands

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes database data)
docker compose down -v

# Rebuild specific service
docker compose build backend
docker compose up -d backend

# Run backend tests
docker compose exec backend pytest

# Run frontend tests
cd frontend && npm test

# Lint backend
cd backend && ruff check .

# Lint frontend
cd frontend && npm run lint

# Format backend
cd backend && ruff format .

# Format frontend
cd frontend && npm run format

# Type check frontend
cd frontend && npm run typecheck

# Access PostgreSQL
docker compose exec postgres psql -U mylife -d mylife

# Access Redis
docker compose exec redis redis-cli
```

## Environment Variables

### Backend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| SECRET_KEY | Yes | - | JWT signing key (32+ chars) |
| DATABASE_URL | Yes | - | PostgreSQL connection string |
| REDIS_URL | Yes | - | Redis connection string |
| OPENAI_API_KEY | No | - | OpenAI API key for AI features |
| ANTHROPIC_API_KEY | No | - | Anthropic API key for AI features |
| CORS_ORIGINS | No | localhost:5173,3000 | Allowed CORS origins |

### Frontend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| VITE_API_URL | Yes | - | Backend GraphQL endpoint |
| VITE_WS_URL | Yes | - | Backend WebSocket endpoint |

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is healthy
docker compose exec postgres pg_isready -U mylife -d mylife

# Check database logs
docker compose logs postgres
```

### Migration Failures

```bash
# Check current migration state
alembic current

# If stuck, manually resolve and stamp
alembic stamp head
```

### Frontend Build Issues

```bash
# Clear node_modules and reinstall
rm -rf frontend/node_modules frontend/package-lock.json
cd frontend && npm install
```

### Port Conflicts

Change ports in `docker-compose.yml` if 5173, 8000, 5432, or 6379 are in use.

## IDE Setup

### VS Code Extensions

- Python (for backend)
- TypeScript/JavaScript (for frontend)
- Tailwind CSS IntelliSense
- GraphQL (for .graphql files)
- Docker
- PostgreSQL

### Debug Configuration

Backend debugging is configured in `.vscode/launch.json`:

```json
{
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      "cwd": "${workspaceFolder}/backend",
      "envFile": "${workspaceFolder}/backend/.env"
    }
  ]
}
```