"""
Custom application exceptions.

Services raise these instead of HTTPException directly, so business logic
stays framework-agnostic. Route handlers / the global exception handler
translate them into HTTP responses.
"""


class AppError(Exception):
    """Base class for all expected, handled application errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ValidationError(AppError):
    """Raised when input fails a business-rule validation check (400)."""


class DuplicateUserError(AppError):
    """Raised when attempting to register an email that already exists (409)."""


class InvalidCredentialsError(AppError):
    """Raised when login email/password do not match (401)."""


class UnauthorizedError(AppError):
    """Raised when a request is missing or has an invalid/expired token (401)."""
