# ADR: Alembic owns the database schema

- Status: Accepted
- Date: 2026-11-25

## Context

Schema creation was split between Alembic and runtime `create_all`, and there
were two `alembic.ini` files. This made migrations ambiguous and risked drift.

## Decision

Alembic is the only schema manager for deployed environments. The backend
container runs `alembic upgrade head` before starting Uvicorn. `init_db()` is a
development-only bootstrap that is skipped outside `ENVIRONMENT=development`.
There is a single `backend/alembic.ini`.

## Consequences

- `docker-compose.yml` runs migrations on backend startup.
- `migrations/env.py` reads `DATABASE_URL` from application settings.
- Production deployments never rely on `Base.metadata.create_all`.
