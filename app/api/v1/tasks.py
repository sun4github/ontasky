from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.common import DueBucket, MessageResponse, TaskStatus, get_user_id
from app.schemas.tasks import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)

router = APIRouter(prefix="/api/v1", tags=["tasks"])


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(req: TaskCreateRequest, user_id: UUID = Depends(get_user_id)):
    """Create a new task. Status defaults to pending."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    user_id: UUID = Depends(get_user_id),
    due: DueBucket | None = Query(default=None, description="Filter by due bucket"),
    project_id: UUID | None = Query(default=None, description="Filter by project"),
    status: TaskStatus | None = Query(default=None, description="Filter by status"),
):
    """List tasks with optional filters. Used by Today/Tomorrow/This Week/Someday views and project views."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Get task detail with all attributes. Used by detailed attributes screen."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    req: TaskUpdateRequest,
    user_id: UUID = Depends(get_user_id),
):
    """Update task attributes (title, note, due_on, project, repeat, etc.)."""
    raise HTTPException(status_code=501, detail="Not implemented")


# ---------------------------------------------------------------------------
# Task state transitions
# ---------------------------------------------------------------------------


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Mark task as completed. Sets status=completed and completed_at."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/tasks/{task_id}/reopen", response_model=TaskResponse)
async def reopen_task(task_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Reopen a completed task. Sets status back to pending."""
    raise HTTPException(status_code=501, detail="Not implemented")


# ---------------------------------------------------------------------------
# Task deletion
# ---------------------------------------------------------------------------


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
async def delete_task(task_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Delete a task and all its subtasks."""
    raise HTTPException(status_code=501, detail="Not implemented")
