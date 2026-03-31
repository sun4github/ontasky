"""Subtask service layer wiring API handlers to DB helpers with auth checks."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException

from app.core import subtasks_db, tasks_db
from app.schemas.subtasks import (
    SubtaskCreateRequest,
    SubtaskReorderRequest,
    SubtaskUpdateRequest,
)


async def create_subtask(task_id: UUID, req: SubtaskCreateRequest, user_id: UUID) -> dict:
    """Create a subtask for an owned task or raise 404."""
    await _require_owned_task(task_id=task_id, user_id=user_id)
    return await subtasks_db.create_subtask(
        task_id=task_id,
        title=req.title,
        sort_order=req.sort_order,
        user_id=user_id,
    )


async def list_subtasks(task_id: UUID, user_id: UUID) -> dict:
    """List subtasks for an owned task or raise 404."""
    await _require_owned_task(task_id=task_id, user_id=user_id)
    return await subtasks_db.list_subtasks(task_id=task_id, user_id=user_id)


async def update_subtask(subtask_id: UUID, req: SubtaskUpdateRequest, user_id: UUID) -> dict:
    """Update a subtask by id for the user or raise 404."""
    update_fields = req.model_dump(exclude_unset=True)
    row = await subtasks_db.update_subtask(
        subtask_id=subtask_id,
        user_id=user_id,
        **update_fields,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return row


async def complete_subtask(subtask_id: UUID, user_id: UUID) -> dict:
    """Mark a subtask completed for the user or raise 404."""
    row = await subtasks_db.complete_subtask(subtask_id=subtask_id, user_id=user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return row


async def reorder_subtasks(task_id: UUID, req: SubtaskReorderRequest, user_id: UUID) -> dict:
    """Reorder subtasks for an owned task.

    The requested IDs must match the owned subtasks for this task exactly.
    """
    await _require_owned_task(task_id=task_id, user_id=user_id)

    existing = await subtasks_db.list_subtasks(task_id=task_id, user_id=user_id)
    existing_ids = [item["id"] for item in existing["items"]]
    requested_ids = req.subtask_ids

    if len(existing_ids) != len(requested_ids) or set(existing_ids) != set(requested_ids):
        raise HTTPException(status_code=404, detail="Subtask not found")

    return await subtasks_db.reorder_subtasks(
        task_id=task_id,
        user_id=user_id,
        subtask_ids=requested_ids,
    )


async def delete_subtask(subtask_id: UUID, user_id: UUID) -> None:
    """Delete a subtask by id for the user or raise 404."""
    deleted = await subtasks_db.delete_subtask(subtask_id=subtask_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subtask not found")


async def _require_owned_task(task_id: UUID, user_id: UUID) -> None:
    task = await tasks_db.get_task(task_id=task_id, user_id=user_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
