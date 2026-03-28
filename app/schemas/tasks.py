from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import RepeatUnit, TaskStatus


class TaskCreateRequest(BaseModel):
    user_id: UUID
    title: str = Field(min_length=1, pattern=r"^[^\r\n]+$")
    project_id: Optional[UUID] = None
    note: Optional[str] = None
    due_on: Optional[date] = None
    repeat_every: Optional[int] = Field(default=None, ge=1, le=10)
    repeat_unit: Optional[RepeatUnit] = None
    created_by_user_id: Optional[UUID] = None

    @model_validator(mode="after")
    def validate_repeat_pair(self) -> TaskCreateRequest:
        has_every = self.repeat_every is not None
        has_unit = self.repeat_unit is not None
        if has_every != has_unit:
            raise ValueError(
                "repeat_every and repeat_unit must both be set or both be null"
            )
        return self


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, pattern=r"^[^\r\n]+$")
    project_id: Optional[UUID] = None
    note: Optional[str] = None
    due_on: Optional[date] = None
    repeat_every: Optional[int] = Field(default=None, ge=1, le=10)
    repeat_unit: Optional[RepeatUnit] = None

    @model_validator(mode="after")
    def validate_repeat_pair(self) -> TaskUpdateRequest:
        has_every = self.repeat_every is not None
        has_unit = self.repeat_unit is not None
        if has_every != has_unit:
            raise ValueError(
                "repeat_every and repeat_unit must both be set or both be null"
            )
        return self


class TaskResponse(BaseModel):
    id: UUID
    user_id: UUID
    project_id: Optional[UUID]
    title: str
    note: Optional[str]
    status: TaskStatus
    pomodoro_count: int
    due_on: Optional[date]
    repeat_every: Optional[int]
    repeat_unit: Optional[RepeatUnit]
    extra: dict
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    started_at: Optional[datetime]
    created_by_user_id: Optional[UUID]


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
