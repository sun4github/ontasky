from uuid import UUID

from fastapi import APIRouter, Depends

from app.schemas.common import MessageResponse, get_user_id
from app.schemas.subtasks import (
    SubtaskCreateRequest,
    SubtaskListResponse,
    SubtaskReorderRequest,
    SubtaskResponse,
    SubtaskUpdateRequest,
)
from app.services import subtasks_service

router = APIRouter(prefix="/api/v1", tags=["subtasks"])


# ---------------------------------------------------------------------------
# Subtask CRUD (nested under task)
# ---------------------------------------------------------------------------


@router.post("/tasks/{task_id}/subtasks", response_model=SubtaskResponse, status_code=201)
async def create_subtask(
    task_id: UUID,
    req: SubtaskCreateRequest,
    user_id: UUID = Depends(get_user_id),
):
    """Add a subtask to a task."""
    return await subtasks_service.create_subtask(task_id=task_id, req=req, user_id=user_id)


@router.get("/tasks/{task_id}/subtasks", response_model=SubtaskListResponse)
async def list_subtasks(task_id: UUID, user_id: UUID = Depends(get_user_id)):
    """List all subtasks for a task, ordered by sort_order."""
    return await subtasks_service.list_subtasks(task_id=task_id, user_id=user_id)


@router.patch("/subtasks/{subtask_id}", response_model=SubtaskResponse)
async def update_subtask(
    subtask_id: UUID,
    req: SubtaskUpdateRequest,
    user_id: UUID = Depends(get_user_id),
):
    """Update subtask title or completion status."""
    return await subtasks_service.update_subtask(subtask_id=subtask_id, req=req, user_id=user_id)


# ---------------------------------------------------------------------------
# Subtask state transitions
# ---------------------------------------------------------------------------


@router.post("/subtasks/{subtask_id}/complete", response_model=SubtaskResponse)
async def complete_subtask(subtask_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Mark a subtask as completed."""
    return await subtasks_service.complete_subtask(subtask_id=subtask_id, user_id=user_id)


# ---------------------------------------------------------------------------
# Subtask ordering
# ---------------------------------------------------------------------------


@router.put("/tasks/{task_id}/subtasks/reorder", response_model=SubtaskListResponse)
async def reorder_subtasks(
    task_id: UUID,
    req: SubtaskReorderRequest,
    user_id: UUID = Depends(get_user_id),
):
    """Reorder subtasks by providing ordered list of subtask IDs."""
    return await subtasks_service.reorder_subtasks(task_id=task_id, req=req, user_id=user_id)


# ---------------------------------------------------------------------------
# Subtask deletion
# ---------------------------------------------------------------------------


@router.delete("/subtasks/{subtask_id}", response_model=MessageResponse)
async def delete_subtask(subtask_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Delete a subtask."""
    await subtasks_service.delete_subtask(subtask_id=subtask_id, user_id=user_id)
    return MessageResponse(detail="Subtask deleted")
