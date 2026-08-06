"""
Authentication dependency (SDD Section 16 - Security).

SDD Section 5 (Assumptions) states that existing platform authentication is
reused rather than redesigned here. This module implements the generic
mechanism - verify a bearer token's signature and expiry, then extract a
client identity - that any reuse of a JWT-based auth system needs. The
claim name used for the client identifier (`sub`) and the absence of
issuer/audience checks are the two things most likely to need adjusting to
match the real platform token schema; everything else is standard JWT
bearer validation and should not need to change.

This module intentionally contains no job-domain logic - only "is this
request authenticated, and who is it from".
"""

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

_bearer_scheme = HTTPBearer(auto_error=True)


@dataclass(frozen=True)
class ClientIdentity:
    client_id: str


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token"
        ) from exc


async def get_current_client(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> ClientIdentity:
    """
    FastAPI dependency for protected routes. Usage:

        @router.post("/jobs")
        async def submit_job(..., client: ClientIdentity = Depends(get_current_client)):
            ...

    Scopes every downstream query (e.g. "list my jobs") to client.client_id,
    enforcing the access-control rule in SDD Section 16: clients may only
    access their own jobs.
    """
    claims = _decode_token(credentials.credentials)
    client_id = claims.get("sub")
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject (client_id) claim",
        )
    return ClientIdentity(client_id=client_id)
