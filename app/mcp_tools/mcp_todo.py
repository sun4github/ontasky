from datetime import date
from uuid import UUID

from fastmcp.tools import tool

from app.schemas.common import (
    DueBucket,
    MessageResponse,
    RepeatUnit,
    TaskStatus,
    get_current_user_from_token,
)
from app.schemas.projects import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.schemas.subtasks import (
    SubtaskCreateRequest,
    SubtaskListResponse,
    SubtaskReorderRequest,
    SubtaskResponse,
    SubtaskUpdateRequest,
)
from app.schemas.tasks import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskUpdateRequest,
)
from app.services import projects_service, subtasks_service, tasks_service


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------


@tool
async def list_tasks(
    token: str,
    due: DueBucket | None = None,
    project_id: UUID | None = None,
    status: TaskStatus | None = None,
) -> TaskListResponse:
    """List active tasks for the authenticated user.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        due: Optional due-date bucket filter (today, tomorrow, this_week, someday, overdue).
        project_id: Optional project filter.
        status: Optional task status filter.

    Returns:
        TaskListResponse with:
        - items: matching task records
        - total: count of returned tasks
    """
    auth_user = await get_current_user_from_token(token)
    result = await tasks_service.list_tasks(
        user_id=auth_user.user_id,
        due=due,
        project_id=project_id,
        status=status,
    )
    return TaskListResponse.model_validate(result)


@tool
async def get_task(token: str, task_id: UUID) -> TaskResponse:
    """Get a single task by ID.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        task_id: The task to retrieve.

    Returns:
        The TaskResponse record.
    """
    auth_user = await get_current_user_from_token(token)
    result = await tasks_service.get_task(task_id=task_id, user_id=auth_user.user_id)
    return TaskResponse.model_validate(result)


@tool
async def create_task(
    token: str,
    title: str,
    project_id: UUID | None = None,
    note: str | None = None,
    due_on: str | None = None,
    repeat_every: int | None = None,
    repeat_unit: RepeatUnit | None = None,
) -> TaskResponse:
    """Create a new task for the authenticated user.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        title: Task title (required, single line).
        project_id: Optional project to assign the task to.
        note: Optional free-text note.
        due_on: Optional due date in YYYY-MM-DD format.
        repeat_every: Optional recurrence interval (1-10). Must be set with repeat_unit.
        repeat_unit: Optional recurrence unit (day, week, month, year). Must be set with repeat_every.

    Returns:
        The created TaskResponse record.
    """
    auth_user = await get_current_user_from_token(token)
    req = TaskCreateRequest(
        title=title,
        project_id=project_id,
        note=note,
        due_on=date.fromisoformat(due_on) if due_on else None,
        repeat_every=repeat_every,
        repeat_unit=repeat_unit,
    )
    result = await tasks_service.create_task(req=req, requester_user_id=auth_user.user_id)
    return TaskResponse.model_validate(result)


@tool
async def update_task(
    token: str,
    task_id: UUID,
    title: str,
    project_id: UUID | None = None,
    note: str | None = None,
    due_on: str | None = None,
    repeat_every: int | None = None,
    repeat_unit: RepeatUnit | None = None,
) -> TaskResponse:
    """Update attributes of an existing task.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        task_id: The task to update.
        title: New title (single line).
        project_id: New project assignment.
        note: New note text.
        due_on: New due date in YYYY-MM-DD format.
        repeat_every: New recurrence interval (1-10). Must be set with repeat_unit.
        repeat_unit: New recurrence unit (day, week, month, year). Must be set with repeat_every.

    Returns:
        The updated TaskResponse record.
    """
    auth_user = await get_current_user_from_token(token)
    req = TaskUpdateRequest(
        title=title,
        project_id=project_id,
        note=note,
        due_on=date.fromisoformat(due_on) if due_on else None,
        repeat_every=repeat_every,
        repeat_unit=repeat_unit,
    )
    result = await tasks_service.update_task(task_id=task_id, req=req, user_id=auth_user.user_id)
    return TaskResponse.model_validate(result)



@tool
async def soft_delete_task(token: str, task_id: UUID) -> TaskResponse:
    """Soft-delete a task (marks is_deleted=true) and hard-deletes all its subtasks.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        task_id: The task to soft-delete.

    Returns:
        The updated TaskResponse record with is_deleted=true.
    """
    auth_user = await get_current_user_from_token(token)
    result = await tasks_service.soft_delete_task(task_id=task_id, user_id=auth_user.user_id)
    return TaskResponse.model_validate(result)


@tool
async def search_tasks(
    token: str,
    q: str,
    limit: int = 20,
    include_completed: bool = False,
    include_deleted: bool = False,
) -> TaskListResponse:
    """Search tasks by title for the authenticated user.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        q: Search query string matched against task titles.
        limit: Maximum number of results to return (default 20).
        include_completed: Include completed tasks in results (default False).
        include_deleted: Include deleted tasks in results (default False).

    Returns:
        TaskListResponse with matching task records and total count.
    """
    auth_user = await get_current_user_from_token(token)
    result = await tasks_service.search_tasks(
        user_id=auth_user.user_id,
        q=q,
        limit=limit,
        include_completed=include_completed,
        include_deleted=include_deleted,
    )
    return TaskListResponse.model_validate(result)


# ---------------------------------------------------------------------------
# Task state transitions
# ---------------------------------------------------------------------------


@tool
async def complete_task(token: str, task_id: UUID) -> TaskResponse:
    """Mark a task as completed.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        task_id: The task to complete.

    Returns:
        The updated TaskResponse record.
    """
    auth_user = await get_current_user_from_token(token)
    result = await tasks_service.complete_task(task_id=task_id, user_id=auth_user.user_id)
    return TaskResponse.model_validate(result)


@tool
async def reopen_task(token: str, task_id: UUID) -> TaskResponse:
    """Reopen a completed task back to pending.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        task_id: The task to reopen.

    Returns:
        The updated TaskResponse record.
    """
    auth_user = await get_current_user_from_token(token)
    result = await tasks_service.reopen_task(task_id=task_id, user_id=auth_user.user_id)
    return TaskResponse.model_validate(result)


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------


@tool
async def list_projects(token: str) -> ProjectListResponse:
    """List active projects for the authenticated user.

    Args:
        token: Raw JWT bearer token for authenticating the caller.

    Returns:
        ProjectListResponse with items and total.
    """
    auth_user = await get_current_user_from_token(token)
    result = await projects_service.list_projects(user_id=auth_user.user_id)
    return ProjectListResponse.model_validate(result)


@tool
async def get_project(token: str, project_id: UUID) -> ProjectResponse:
    """Get a single project by ID.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        project_id: The project to retrieve.

    Returns:
        The ProjectResponse record.
    """
    auth_user = await get_current_user_from_token(token)
    result = await projects_service.get_project(project_id=project_id, user_id=auth_user.user_id)
    return ProjectResponse.model_validate(result)


@tool
async def search_projects(
    token: str,
    q: str,
    limit: int = 20,
    include_completed: bool = False,
    include_deleted: bool = False,
) -> ProjectListResponse:
    """Search projects by path for the authenticated user.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        q: Search query string matched against the leaf path segment.
        limit: Maximum number of results to return (default 20).
        include_completed: Include completed projects in results (default False).
        include_deleted: Include deleted projects in results (default False).

    Returns:
        ProjectListResponse with matching project records and total count.
    """
    auth_user = await get_current_user_from_token(token)
    result = await projects_service.search_projects(
        user_id=auth_user.user_id,
        q=q,
        limit=limit,
        include_completed=include_completed,
        include_deleted=include_deleted,
    )
    return ProjectListResponse.model_validate(result)


@tool
async def create_project(token: str, path: str) -> ProjectResponse:
    """Create a new project.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        path: Project path supporting '/' for hierarchy (e.g. 'Work/Engineering').

    Returns:
        The created ProjectResponse record.
    """
    auth_user = await get_current_user_from_token(token)
    req = ProjectCreateRequest(path=path)
    result = await projects_service.create_project(req=req, user_id=auth_user.user_id)
    return ProjectResponse.model_validate(result)


@tool
async def update_project(token: str, project_id: UUID, path: str) -> ProjectResponse:
    """Rename or move a project by updating its path.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        project_id: The project to update.
        path: New project path.

    Returns:
        The updated ProjectResponse record.
    """
    auth_user = await get_current_user_from_token(token)
    req = ProjectUpdateRequest(path=path)
    result = await projects_service.update_project(
        project_id=project_id, req=req, user_id=auth_user.user_id,
    )
    return ProjectResponse.model_validate(result)



@tool
async def soft_delete_project(token: str, project_id: UUID) -> ProjectResponse:
    """Soft-delete a project (marks is_deleted=true), soft-deletes all its tasks, and hard-deletes their subtasks.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        project_id: The project to soft-delete.

    Returns:
        The updated ProjectResponse record with is_deleted=true.
    """
    auth_user = await get_current_user_from_token(token)
    result = await projects_service.soft_delete_project(project_id=project_id, user_id=auth_user.user_id)
    return ProjectResponse.model_validate(result)


@tool
async def complete_project(token: str, project_id: UUID) -> ProjectResponse:
    """Mark a project as completed (sets is_completed=true).

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        project_id: The project to complete.

    Returns:
        The updated ProjectResponse record with is_completed=true.
    """
    auth_user = await get_current_user_from_token(token)
    result = await projects_service.complete_project(project_id=project_id, user_id=auth_user.user_id)
    return ProjectResponse.model_validate(result)


# ---------------------------------------------------------------------------
# Subtask CRUD
# ---------------------------------------------------------------------------


@tool
async def list_subtasks(token: str, task_id: UUID) -> SubtaskListResponse:
    """List all subtasks for a task, ordered by sort_order.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        task_id: The parent task.

    Returns:
        SubtaskListResponse with items and total.
    """
    auth_user = await get_current_user_from_token(token)
    result = await subtasks_service.list_subtasks(task_id=task_id, user_id=auth_user.user_id)
    return SubtaskListResponse.model_validate(result)


@tool
async def create_subtask(
    token: str,
    task_id: UUID,
    title: str,
    sort_order: int = 0,
) -> SubtaskResponse:
    """Add a subtask to a task.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        task_id: The parent task.
        title: Subtask title (required, single line).
        sort_order: Position in the subtask list (default 0).

    Returns:
        The created SubtaskResponse record.
    """
    auth_user = await get_current_user_from_token(token)
    req = SubtaskCreateRequest(title=title, sort_order=sort_order)
    result = await subtasks_service.create_subtask(task_id=task_id, req=req, user_id=auth_user.user_id)
    return SubtaskResponse.model_validate(result)


@tool
async def update_subtask(
    token: str,
    subtask_id: UUID,
    title: str | None = None,
    is_completed: bool | None = None,
) -> SubtaskResponse:
    """Update a subtask's title or completion status.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        subtask_id: The subtask to update.
        title: New title (single line).
        is_completed: Set completion status.

    Returns:
        The updated SubtaskResponse record.
    """
    auth_user = await get_current_user_from_token(token)
    req = SubtaskUpdateRequest(title=title, is_completed=is_completed)
    result = await subtasks_service.update_subtask(subtask_id=subtask_id, req=req, user_id=auth_user.user_id)
    return SubtaskResponse.model_validate(result)


@tool
async def complete_subtask(token: str, subtask_id: UUID) -> SubtaskResponse:
    """Mark a subtask as completed.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        subtask_id: The subtask to complete.

    Returns:
        The updated SubtaskResponse record.
    """
    auth_user = await get_current_user_from_token(token)
    result = await subtasks_service.complete_subtask(subtask_id=subtask_id, user_id=auth_user.user_id)
    return SubtaskResponse.model_validate(result)


# ---------------------------------------------------------------------------
# Subtask ordering
# ---------------------------------------------------------------------------


@tool
async def reorder_subtasks(
    token: str,
    task_id: UUID,
    subtask_ids: list[UUID],
) -> SubtaskListResponse:
    """Reorder subtasks by providing an ordered list of subtask IDs.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        task_id: The parent task.
        subtask_ids: Ordered list of subtask IDs defining the new sort order.

    Returns:
        SubtaskListResponse with the reordered subtasks.
    """
    auth_user = await get_current_user_from_token(token)
    req = SubtaskReorderRequest(subtask_ids=subtask_ids)
    result = await subtasks_service.reorder_subtasks(task_id=task_id, req=req, user_id=auth_user.user_id)
    return SubtaskListResponse.model_validate(result)


@tool
async def delete_subtask(token: str, subtask_id: UUID) -> MessageResponse:
    """Delete a subtask.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        subtask_id: The subtask to delete.

    Returns:
        Confirmation message.
    """
    auth_user = await get_current_user_from_token(token)
    await subtasks_service.delete_subtask(subtask_id=subtask_id, user_id=auth_user.user_id)
    return MessageResponse(detail="Subtask deleted")