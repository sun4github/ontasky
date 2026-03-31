"""Project service layer wiring API handlers to DB helpers."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException

from app.core import projects_db
from app.schemas.projects import ProjectCreateRequest, ProjectUpdateRequest


async def create_project(req: ProjectCreateRequest, user_id: UUID) -> dict:
    """Create a project for the user and return the created row."""
    return await projects_db.create_project(user_id=user_id, path=req.path)


async def list_projects(user_id: UUID) -> dict:
    """List projects for the user."""
    return await projects_db.list_projects(user_id=user_id)


async def get_project(project_id: UUID, user_id: UUID) -> dict:
    """Get a project by id for a user or raise 404."""
    row = await projects_db.get_project(project_id=project_id, user_id=user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return row


async def update_project(project_id: UUID, req: ProjectUpdateRequest, user_id: UUID) -> dict:
    """Update a project path and return the updated row or raise 404."""
    row = await projects_db.update_project(
        project_id=project_id,
        user_id=user_id,
        path=req.path,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return row


async def delete_project(project_id: UUID, user_id: UUID) -> None:
    """Delete a project or raise 404 if no row is found."""
    deleted = await projects_db.delete_project(project_id=project_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
