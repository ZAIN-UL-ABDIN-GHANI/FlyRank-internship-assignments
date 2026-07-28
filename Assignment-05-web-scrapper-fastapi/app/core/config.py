"""Environment-based application configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "scraper-service"
    app_env: str = "development"
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str = "sqlite:///./dev.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Responsible crawling (config surface consumed starting Phase 3+)
    user_agent: str = "scraper-service-bot/1.0"
    request_rate_limit_delay_seconds: float = 1.5
    max_retries: int = 3


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance -- single source of truth for config."""
    return Settings()
