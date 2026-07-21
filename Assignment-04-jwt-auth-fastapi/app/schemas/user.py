"""
Pydantic schemas for user registration and API responses.
"""
import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Payload for POST /register."""

    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("full_name cannot be empty or whitespace")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("password must contain at least one digit")
        return v


class UserResponse(BaseModel):
    """Safe user representation returned by the API. Never includes the password."""

    id: str
    full_name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}
