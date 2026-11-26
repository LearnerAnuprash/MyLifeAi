"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter
import structlog

from app.core.config import get_settings
from app.db.session import close_db, init_db
from app.graphql.schema import schema
from app.graphql.context import get_context

settings = get_settings()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.is_production else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting application", environment=settings.ENVIRONMENT)
    # Development bootstrap only; production uses `alembic upgrade head`.
    try:
        await init_db()
    except Exception as exc:
        logger.warning("Database bootstrap skipped", error=str(exc))

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="My Life AI - Intelligent Personal Life Management Platform",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.cors_allow_methods_list,
        allow_headers=settings.cors_allow_headers_list,
    )

    # GraphQL router
    graphql_app = GraphQLRouter(
        schema,
        context_getter=get_context,
    )
    app.include_router(graphql_app, prefix=settings.GRAPHQL_PATH)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "graphql": settings.GRAPHQL_PATH,
            "docs": "/docs" if settings.DEBUG else "disabled",
        }

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
            },
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )