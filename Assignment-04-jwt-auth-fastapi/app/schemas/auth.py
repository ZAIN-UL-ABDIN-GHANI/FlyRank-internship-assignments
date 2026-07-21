"""
Pydantic schemas for authentication (login + token responses).
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Payload for POST /login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Response returned after a successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
