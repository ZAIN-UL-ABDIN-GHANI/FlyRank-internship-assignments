"""
Centralized application configuration.

All runtime configuration is sourced from environment variables (see
.env.example for the full list and SDD Section 5 - Assumptions / Section 16
- Security for why secrets are injected rather than hardcoded). Importing
`settings` anywhere in the app gives a single, validated source of truth -
if a required variable is missing or malformed, the app fails at startup
instead of failing on the first request that touches it.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "job-processing-service"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/v1"

    # --- Persistence layer (SDD Section 7.4) ---
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 5

    # --- Queue / broker + cache layer (SDD Section 7.2, 7.5) ---
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    STATUS_CACHE_TTL_SECONDS: int = 30

    # --- Retry strategy defaults (SDD Section 10) ---
    JOB_DEFAULT_MAX_RETRIES: int = 5
    JOB_RETRY_BASE_DELAY_SECONDS: int = 2
    JOB_RETRY_MAX_DELAY_SECONDS: int = 32

    # --- Data retention (SDD NFR8) ---
    JOB_RETENTION_DAYS: int = 30

    # --- Security (SDD Section 16) ---
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    RATE_LIMIT_PER_MINUTE: int = 60
    CORS_ORIGINS: str = "http://localhost:3000"
    MAX_PAYLOAD_SIZE_BYTES: int = 65536
    # Placeholder default of just the one operation used throughout the SDD's
    # examples - this MUST be updated to match whatever operations the real
    # AI pipeline actually supports (SDD Section 4 keeps those internals out
    # of scope, so this app has no way to know the real list on its own).
    ALLOWED_OPERATIONS: str = "rag_query"

    # --- Logging (SDD Section 17) ---
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor - env is read once per process."""
    return Settings()


settings = get_settings()
