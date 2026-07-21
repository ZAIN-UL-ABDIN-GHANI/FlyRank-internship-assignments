"""
Reusable authentication dependency ("middleware").

This is the SINGLE place JWT validation happens. Any protected route
just declares `current_user: User = Depends(get_current_user)` and gets:
  - Authorization header presence check
  - "Bearer <token>" scheme check
  - Signature + expiration verification
  - The authenticated User loaded from the DB, attached to the request

No route or controller re-implements any of this logic.
"""
import jwt
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise UnauthorizedError("Missing Authorization header")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Authorization header must be in the form: Bearer <token>")

    token = parts[1]

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedError("User for this token no longer exists")

    return user
