"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "My Life AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = True
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8

    # Database
    DATABASE_URL: str = Field(..., pattern=r"^postgresql(\+asyncpg)?://")
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 5
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", pattern="^redis://")
    REDIS_MAX_CONNECTIONS: int = 50

    # CORS - stored as strings, parsed via properties
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    CORS_ALLOW_HEADERS: str = "*"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def cors_allow_methods_list(self) -> List[str]:
        return [method.strip() for method in self.CORS_ALLOW_METHODS.split(",")]

    @property
    def cors_allow_headers_list(self) -> List[str]:
        return [header.strip() for header in self.CORS_ALLOW_HEADERS.split(",")]

    # GraphQL
    GRAPHQL_PATH: str = "/graphql"
    GRAPHQL_PLAYGROUND: bool = True

    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", pattern="^redis://")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", pattern="^redis://")
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 300
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 4

    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    # AI/LLM
    DEFAULT_AI_PROVIDER: str = "openai"
    DEFAULT_AI_MODEL: str = "gpt-4o"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Email (for future use)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "My Life AI"

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: str = "1minute"

    # File uploads
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "/tmp/uploads"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()