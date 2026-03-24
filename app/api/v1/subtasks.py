from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.common import MessageResponse, get_user_id
from app.schemas.subtasks import (
    SubtaskCreateRequest,
    SubtaskListResponse,
    SubtaskReorderRequest,
    SubtaskResponse,
    SubtaskUpdateRequest,
)

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
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/tasks/{task_id}/subtasks", response_model=SubtaskListResponse)
async def list_subtasks(task_id: UUID, user_id: UUID = Depends(get_user_id)):
    """List all subtasks for a task, ordered by sort_order."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.patch("/subtasks/{subtask_id}", response_model=SubtaskResponse)
async def update_subtask(
    subtask_id: UUID,
    req: SubtaskUpdateRequest,
    user_id: UUID = Depends(get_user_id),
):
    """Update subtask title or completion status."""
    raise HTTPException(status_code=501, detail="Not implemented")


# ---------------------------------------------------------------------------
# Subtask state transitions
# ---------------------------------------------------------------------------


@router.post("/subtasks/{subtask_id}/complete", response_model=SubtaskResponse)
async def complete_subtask(subtask_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Mark a subtask as completed."""
    raise HTTPException(status_code=501, detail="Not implemented")


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
    raise HTTPException(status_code=501, detail="Not implemented")


# ---------------------------------------------------------------------------
# Subtask deletion
# ---------------------------------------------------------------------------


@router.delete("/subtasks/{subtask_id}", response_model=MessageResponse)
async def delete_subtask(subtask_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Delete a subtask."""
    raise HTTPException(status_code=501, detail="Not implemented")
