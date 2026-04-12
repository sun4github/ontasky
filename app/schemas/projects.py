from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

_PATH_PATTERN = r"^[^/\s][^/]*(/[^/\s][^/]*)*$"


class ProjectCreateRequest(BaseModel):
    path: str = Field(min_length=1, pattern=_PATH_PATTERN)


class ProjectUpdateRequest(BaseModel):
    path: str = Field(min_length=1, pattern=_PATH_PATTERN)


class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    path: str
    created_at: datetime
    is_deleted: bool
    is_completed: bool

    @computed_field
    @property
    def name(self) -> str:
        return self.path.rsplit("/", 1)[-1]

    @computed_field
    @property
    def depth(self) -> int:
        return self.path.count("/") + 1


class ProjectTreeNode(BaseModel):
    id: Optional[UUID] = None
    path: str
    name: str
    children: list[ProjectTreeNode] = Field(default_factory=list)


ProjectTreeNode.model_rebuild()


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
