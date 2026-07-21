"""
Authentication business logic.

Routes call into this service; the service never knows about HTTP —
it raises AppError subclasses which the global exception handler
converts into the right HTTP response.
"""
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateUserError, InvalidCredentialsError
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import hash_password, verify_password, create_access_token


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def register_user(db: Session, payload: UserCreate) -> User:
    """
    Create a new user with a bcrypt-hashed password.

    Raises DuplicateUserError if the email is already registered.
    """
    existing_user = get_user_by_email(db, payload.email)
    if existing_user is not None:
        raise DuplicateUserError(f"A user with email '{payload.email}' already exists")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> str:
    """
    Verify credentials and return a signed JWT access token.

    Raises InvalidCredentialsError if the email doesn't exist or the
    password doesn't match. Deliberately uses the same error message for
    both cases so we don't leak which emails are registered.
    """
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError("Invalid email or password")

    return create_access_token(subject=user.id)
