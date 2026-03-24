from enum import Enum
from typing import Annotated
from uuid import UUID

from fastapi import Header, HTTPException
from pydantic import BaseModel


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


async def get_user_id(x_user_id: Annotated[str, Header()]) -> UUID:
    """Extract and validate user_id from X-User-Id header."""
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header")
