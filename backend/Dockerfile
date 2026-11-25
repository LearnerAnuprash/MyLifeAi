# Backend Dockerfile - Multi-stage build
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install uv for fast package management
RUN pip install --no-cache-dir uv

# Copy dependency files first (for better layer caching)
COPY pyproject.toml uv.lock* ./

# Development stage
FROM base as development

# Install development dependencies
RUN uv pip install --system -e ".[dev]"

# Copy source code
COPY ./migrations ./migrations
COPY ./app ./app
COPY ./alembic.ini ./migrations/alembic.ini

# Ensure alembic.ini is readable
RUN chmod 644 ./migrations/alembic.ini

# Expose port
EXPOSE 8000

# Production stage
FROM base as production

# Install production dependencies only
RUN uv pip install --system -e .

# Copy source code
COPY ./migrations ./migrations
COPY ./app ./app
COPY ./alembic.ini ./migrations/alembic.ini

# Ensure alembic.ini is readable
RUN chmod 644 ./migrations/alembic.ini

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]