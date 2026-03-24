from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserSettingsUpdateRequest(BaseModel):
    pomodoro_mins: Optional[int] = Field(default=None, ge=1, le=180)
    break_mins: Optional[int] = Field(default=None, ge=1, le=120)
    timezone: Optional[str] = None
    alert_sound: Optional[str] = None


class UserSettingsResponse(BaseModel):
    user_id: UUID
    alert_sound: str
    pomodoro_mins: int
    break_mins: int
    timezone: str
    updated_at: datetime
