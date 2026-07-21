"""
Low-level security primitives: password hashing (bcrypt) and JWT
encoding/decoding (PyJWT). No business logic lives here.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hash a plain-text password with a bcrypt salt. Returns a utf-8 string."""
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against a stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def create_access_token(subject: str) -> str:
    """
    Create a signed JWT for the given subject (we use the user's id).

    Standard claims used:
      - sub: subject (user id)
      - iat: issued-at
      - exp: expiration
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT.

    Raises jwt.ExpiredSignatureError if expired, or jwt.InvalidTokenError
    (and subclasses) for any other invalid-token condition. Callers are
    expected to catch these and translate them into 401 responses.
    """
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
