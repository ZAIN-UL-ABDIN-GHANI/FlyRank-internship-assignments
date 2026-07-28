"""Base application exceptions.

Domain-specific exceptions are added alongside the components that raise
them (e.g., fetch/parse errors land in `app.scraping` in a later phase).
"""


class AppError(Exception):
    """Base class for all application-specific errors."""


class ConfigurationError(AppError):
    """Raised when required configuration is missing or invalid."""
