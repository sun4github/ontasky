from enum import Enum
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.auth import AuthTokenError, decode_access_token
from app.core.users_db import upsert_app_user  # add this


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class RepeatUnit(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    year = "year"


class DueBucket(str, Enum):
    """Filter tasks by due date category."""

    today = "today"
    tomorrow = "tomorrow"
    this_week = "this_week"
    someday = "someday"


class MessageResponse(BaseModel):
    detail: str


class AuthenticatedUser(BaseModel):
    user_id: UUID
    username: str | None = None


bearer_scheme = HTTPBearer(auto_error=False)


async def get_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UUID:
    """Extract and validate user_id from an Authorization Bearer token."""
    return (await get_current_user(credentials)).user_id


async def get_current_user_from_token(token: str) -> AuthenticatedUser:
    """Extract user identity and optional username from a raw JWT token."""
    auth_headers = {"WWW-Authenticate": "Bearer"}

    try:
        claims = decode_access_token(token)
    except AuthTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers=auth_headers,
        )

    sub = claims.get("sub")
    if not isinstance(sub, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
            headers=auth_headers,
        )

    try:
        user_id = UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject claim in access token",
            headers=auth_headers,
        )

    username = claims.get("username")
    if username is not None and not isinstance(username, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username claim in access token",
            headers=auth_headers,
        )

    # Ensure the user exists in the database
    if claims.get("token_kind", "human") == "human":
        await upsert_app_user(user_id=user_id, username=username)

    return AuthenticatedUser(user_id=user_id, username=username)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthenticatedUser:
    """Extract user identity and optional username from a Bearer token."""
    auth_headers = {"WWW-Authenticate": "Bearer"}
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer token",
            headers=auth_headers,
        )

    return await get_current_user_from_token(credentials.credentials)
