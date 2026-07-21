"""
Protected user routes.
"""
from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the currently authenticated user's profile.

    Requires a valid Bearer token. Never exposes the password hash —
    UserResponse simply doesn't include that field.
    """
    return current_user
