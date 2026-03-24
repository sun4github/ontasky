from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.common import MessageResponse, get_user_id
from app.schemas.projects import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)

router = APIRouter(prefix="/api/v1", tags=["projects"])


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(req: ProjectCreateRequest, user_id: UUID = Depends(get_user_id)):
    """Create a project. Path supports '/' for hierarchy (e.g. 'Work/Engineering')."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(user_id: UUID = Depends(get_user_id)):
    """List all projects for the user in flat and tree views."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Get a single project by ID."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    req: ProjectUpdateRequest,
    user_id: UUID = Depends(get_user_id),
):
    """Rename/move a project by updating its path."""
    raise HTTPException(status_code=501, detail="Not implemented")


# ---------------------------------------------------------------------------
# Project deletion
# ---------------------------------------------------------------------------


@router.delete("/projects/{project_id}", response_model=MessageResponse)
async def delete_project(project_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Delete a project. Tasks in this project will have their project_id set to null."""
    raise HTTPException(status_code=501, detail="Not implemented")
