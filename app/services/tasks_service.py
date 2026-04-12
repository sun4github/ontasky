"""Task service layer wiring API handlers to DB helpers with auth checks."""

from __future__ import annotations

import hashlib, hmac
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException

from app.core import assigners_db, tasks_db
from app.schemas.common import DueBucket, TaskStatus
from app.schemas.tasks import TaskCreateRequest, TaskUpdateRequest


async def create_task(
    req: TaskCreateRequest,
    requester_user_id: UUID,
    assigner_key: str | None = None,
) -> dict:
    """Create a task after ownership and delegation checks.

    When ``req.user_id`` is omitted or matches the requester the task is a
    self-create and no delegation check is needed.

    When ``req.user_id`` differs from the requester, the caller must supply a
    valid ``X-Assigner-Key`` header and have an active grant from the target
    user.  In that case ``created_by_user_id`` is forced to the requester.
    """
    target_user_id = req.user_id if req.user_id is not None else requester_user_id
    is_self_create = target_user_id == requester_user_id

    if not is_self_create:
        if assigner_key is None:
            raise HTTPException(
                status_code=400,
                detail="X-Assigner-Key header is required when creating tasks for another user",
            )

        await _require_valid_assigner_key(
            assigner_user_id=requester_user_id,
            raw_key=assigner_key,
        )
        await _require_create_task_grant(
            user_id=target_user_id,
            assigner_user_id=requester_user_id,
        )

    created_by_user_id = (
        requester_user_id
        if not is_self_create
        else (req.created_by_user_id or requester_user_id)
    )

    return await tasks_db.create_task(
        user_id=target_user_id,
        title=req.title,
        project_id=req.project_id,
        note=req.note,
        due_on=req.due_on,
        repeat_every=req.repeat_every,
        repeat_unit=req.repeat_unit,
        created_by_user_id=created_by_user_id,
    )


async def list_tasks(
    user_id: UUID,
    due: DueBucket | None = None,
    project_id: UUID | None = None,
    status: TaskStatus | None = None,
) -> dict:
    """List tasks for a user with optional filters."""
    return await tasks_db.list_tasks(
        user_id=user_id,
        due=due.value if due is not None else None,
        project_id=project_id,
        status=status.value if status is not None else None,
    )


async def search_tasks(
    user_id: UUID,
    q: str,
    limit: int = 20,
    include_completed: bool = False,
    include_deleted: bool = False,
) -> dict:
    """Search tasks by title for a user with deterministic ordering."""
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    return await tasks_db.search_tasks(
        user_id=user_id,
        q=query,
        limit=limit,
        include_completed=include_completed,
        include_deleted=include_deleted,
    )


async def get_task(task_id: UUID, user_id: UUID) -> dict:
    """Get a task by id for a user or raise 404."""
    row = await tasks_db.get_task(task_id=task_id, user_id=user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


async def update_task(task_id: UUID, req: TaskUpdateRequest, user_id: UUID) -> dict:
    """Update a task and return the updated row or raise 404."""
    row = await tasks_db.update_task(
        task_id=task_id,
        user_id=user_id,
        title=req.title,
        project_id=req.project_id,
        note=req.note,
        due_on=req.due_on,
        repeat_every=req.repeat_every,
        repeat_unit=req.repeat_unit,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


async def complete_task(task_id: UUID, user_id: UUID) -> dict:
    """Mark a task complete or raise 404 if no row is found."""
    row = await tasks_db.complete_task(task_id=task_id, user_id=user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


async def reopen_task(task_id: UUID, user_id: UUID) -> dict:
    """Reopen a task or raise 404 if no row is found."""
    row = await tasks_db.reopen_task(task_id=task_id, user_id=user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


async def delete_task(task_id: UUID, user_id: UUID) -> None:
    """Delete a task or raise 404 if no row is found."""
    deleted = await tasks_db.delete_task(task_id=task_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")


async def soft_delete_task(task_id: UUID, user_id: UUID) -> dict:
    """Mark a task as deleted (soft delete) and hard-delete its subtasks."""
    row = await tasks_db.soft_delete_task(task_id=task_id, user_id=user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


async def _require_valid_assigner_key(assigner_user_id: UUID, raw_key: str) -> None:
    credentials = await assigners_db.list_active_assigner_credentials(assigner_user_id)
    candidate_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    for credential in credentials.get("items", []):
        # Use constant-time comparison to prevent timing attacks
        if hmac.compare_digest(credential.get("key_hash", ""), candidate_hash):
            return

    raise HTTPException(status_code=403, detail="Invalid assigner key")


async def _require_create_task_grant(user_id: UUID, assigner_user_id: UUID) -> None:
    grant = await assigners_db.get_task_assigner_grant(user_id, assigner_user_id)
    if not _grant_allows_create_task(grant):
        raise HTTPException(status_code=403, detail="Not authorized to create task")


def _grant_allows_create_task(grant: dict | None) -> bool:
    if grant is None:
        return False

    if grant.get("revoked_at") is not None:
        return False

    expires_at = grant.get("expires_at")
    if isinstance(expires_at, datetime):
        if expires_at.tzinfo is None:
            now = datetime.utcnow()
        else:
            now = datetime.now(timezone.utc)
        if expires_at <= now:
            return False

    permissions = grant.get("permissions")
    if not isinstance(permissions, dict):
        return False

    return permissions.get("create_task") is True
