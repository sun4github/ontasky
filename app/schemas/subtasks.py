from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SubtaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, pattern=r"^[^\r\n]+$")
    sort_order: int = Field(default=0, ge=0)


class SubtaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, pattern=r"^[^\r\n]+$")
    is_completed: Optional[bool] = None


class SubtaskReorderRequest(BaseModel):
    subtask_ids: list[UUID]


class SubtaskResponse(BaseModel):
    id: UUID
    task_id: UUID
    title: str
    is_completed: bool
    sort_order: int
    created_at: datetime
    completed_at: Optional[datetime]


class SubtaskListResponse(BaseModel):
    items: list[SubtaskResponse]
    total: int
