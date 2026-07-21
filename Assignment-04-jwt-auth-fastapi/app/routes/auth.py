"""
Authentication routes: registration and login.

Route handlers stay thin — validation is handled by Pydantic schemas,
business logic lives in app.services.auth_service.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service
from app.core.config import settings

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    - 201: user created, returns the safe user representation
    - 400: validation error (handled automatically by Pydantic/FastAPI)
    - 409: email already registered
    """
    user = auth_service.register_user(db, payload)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and issue a JWT access token.

    - 200: returns the access token
    - 401: invalid email or password
    """
    token = auth_service.authenticate_user(db, payload.email, payload.password)
    return TokenResponse(access_token=token, expires_in_minutes=settings.jwt_expire_minutes)
