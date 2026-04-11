from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query

from app.schemas.common import DueBucket, MessageResponse, TaskStatus, get_user_id
from app.schemas.tasks import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)
from app.services import tasks_service

router = APIRouter(prefix="/api/v1", tags=["tasks"])


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    req: TaskCreateRequest,
    user_id: UUID = Depends(get_user_id),
    x_assigner_key: str | None = Header(default=None),
):
    """Create a new task. Status defaults to pending."""
    return await tasks_service.create_task(
        req=req,
        requester_user_id=user_id,
        assigner_key=x_assigner_key,
    )


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    user_id: UUID = Depends(get_user_id),
    due: DueBucket | None = Query(default=None, description="Filter by due bucket"),
    project_id: UUID | None = Query(default=None, description="Filter by project"),
    status: TaskStatus | None = Query(default=None, description="Filter by status"),
):
    """List tasks with optional filters. Used by Today/Tomorrow/This Week/Someday views and project views."""
    return await tasks_service.list_tasks(
        user_id=user_id,
        due=due,
        project_id=project_id,
        status=status,
    )


@router.get("/tasks/search", response_model=TaskListResponse)
async def search_tasks(
    q: str = Query(..., description="Search query for task title"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    user_id: UUID = Depends(get_user_id),
):
    """Search tasks by title for the current user."""
    return await tasks_service.search_tasks(user_id=user_id, q=q, limit=limit)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Get task detail with all attributes. Used by detailed attributes screen."""
    return await tasks_service.get_task(task_id=task_id, user_id=user_id)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    req: TaskUpdateRequest,
    user_id: UUID = Depends(get_user_id),
):
    """Update task attributes (title, note, due_on, project, repeat, etc.)."""
    return await tasks_service.update_task(task_id=task_id, req=req, user_id=user_id)


# ---------------------------------------------------------------------------
# Task state transitions
# ---------------------------------------------------------------------------


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Mark task as completed. Sets status=completed and completed_at."""
    return await tasks_service.complete_task(task_id=task_id, user_id=user_id)


@router.post("/tasks/{task_id}/reopen", response_model=TaskResponse)
async def reopen_task(task_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Reopen a completed task. Sets status back to pending."""
    return await tasks_service.reopen_task(task_id=task_id, user_id=user_id)


# ---------------------------------------------------------------------------
# Task deletion
# ---------------------------------------------------------------------------


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
async def delete_task(task_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Delete a task and all its subtasks."""
    await tasks_service.delete_task(task_id=task_id, user_id=user_id)
    return MessageResponse(detail="Task deleted")
