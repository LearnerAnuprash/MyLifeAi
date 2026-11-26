# Backend Dockerfile - Multi-stage build
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for fast package management
RUN pip install --no-cache-dir uv

# Copy dependency manifest first (better layer caching).
COPY pyproject.toml uv.lock* ./

# Source must exist before the editable install so package discovery succeeds.
COPY ./app ./app
COPY ./migrations ./migrations
COPY ./alembic.ini ./alembic.ini

ENV PYTHONPATH=/app

# Development stage
FROM base AS development

RUN uv pip install --system -e ".[dev]"

EXPOSE 8000

# Production stage
FROM base AS production

RUN uv pip install --system -e .

RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
