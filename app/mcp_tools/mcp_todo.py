from uuid import UUID

from fastmcp.tools import tool
from app.schemas.common import DueBucket, TaskStatus, get_current_user_from_token
from app.schemas.tasks import TaskListResponse
from app.services import tasks_service


@tool
async def list_tasks(
    token: str,
    due: DueBucket | None = None,
    project_id: UUID | None = None,
    status: TaskStatus | None = None,
) -> TaskListResponse:
    """List tasks for the authenticated user.

    Args:
        token: Raw JWT bearer token for authenticating the caller.
        due: Optional due-date bucket filter (today, tomorrow, this_week, someday).
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