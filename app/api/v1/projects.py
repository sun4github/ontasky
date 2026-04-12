from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.schemas.common import MessageResponse, get_user_id
from app.schemas.projects import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services import projects_service

router = APIRouter(prefix="/api/v1", tags=["projects"])


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(req: ProjectCreateRequest, user_id: UUID = Depends(get_user_id)):
    """Create a project. Path supports '/' for hierarchy (e.g. 'Work/Engineering')."""
    return await projects_service.create_project(req=req, user_id=user_id)


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(user_id: UUID = Depends(get_user_id)):
    """List all projects for the user in flat and tree views."""
    return await projects_service.list_projects(user_id=user_id)


@router.get("/projects/search", response_model=ProjectListResponse)
async def search_projects(
    q: str = Query(..., description="Search query for project name"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    include_completed: bool = Query(default=False, description="Include completed projects"),
    include_deleted: bool = Query(default=False, description="Include deleted projects"),
    user_id: UUID = Depends(get_user_id),
):
    """Search projects by leaf path name for the current user."""
    return await projects_service.search_projects(
        user_id=user_id,
        q=q,
        limit=limit,
        include_completed=include_completed,
        include_deleted=include_deleted,
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Get a single project by ID."""
    return await projects_service.get_project(project_id=project_id, user_id=user_id)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    req: ProjectUpdateRequest,
    user_id: UUID = Depends(get_user_id),
):
    """Rename/move a project by updating its path."""
    return await projects_service.update_project(
        project_id=project_id,
        req=req,
        user_id=user_id,
    )


# ---------------------------------------------------------------------------
# Project deletion
# ---------------------------------------------------------------------------

@router.post("/projects/{project_id}/delete", response_model=ProjectResponse)
async def soft_delete_project(project_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Soft-delete a project (sets is_deleted=true). Soft-deletes all its tasks and hard-deletes their subtasks."""
    return await projects_service.soft_delete_project(project_id=project_id, user_id=user_id)


@router.post("/projects/{project_id}/complete", response_model=ProjectResponse)
async def complete_project(project_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Mark a project as completed (sets is_completed=true)."""
    return await projects_service.complete_project(project_id=project_id, user_id=user_id)
