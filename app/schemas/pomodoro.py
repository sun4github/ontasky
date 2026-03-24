from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PomodoroStartRequest(BaseModel):
    task_id: UUID


class PomodoroStopRequest(BaseModel):
    completed: bool = True


class PomodoroSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    task_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    work_seconds: int
    break_seconds: int
    completed: bool


class PomodoroSessionListResponse(BaseModel):
    items: list[PomodoroSessionResponse]
    total: int
