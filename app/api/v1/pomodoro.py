from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.common import get_user_id
from app.schemas.pomodoro import (
    PomodoroSessionListResponse,
    PomodoroSessionResponse,
    PomodoroStartRequest,
    PomodoroStopRequest,
)

router = APIRouter(prefix="/api/v1", tags=["pomodoro"])


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------


@router.post("/pomodoro/start", response_model=PomodoroSessionResponse, status_code=201)
async def start_pomodoro(req: PomodoroStartRequest, user_id: UUID = Depends(get_user_id)):
    """Start a pomodoro session for a task. Sets task status to in_progress."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/pomodoro/{session_id}/stop", response_model=PomodoroSessionResponse)
async def stop_pomodoro(
    session_id: UUID,
    req: PomodoroStopRequest,
    user_id: UUID = Depends(get_user_id),
):
    """Stop/complete a pomodoro session. If completed=true, increments task pomodoro_count."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/pomodoro/{session_id}/pause", response_model=PomodoroSessionResponse)
async def pause_pomodoro(session_id: UUID, user_id: UUID = Depends(get_user_id)):
    """Pause a running pomodoro session."""
    raise HTTPException(status_code=501, detail="Not implemented")


# ---------------------------------------------------------------------------
# Session queries
# ---------------------------------------------------------------------------


@router.get("/pomodoro/active", response_model=PomodoroSessionResponse | None)
async def get_active_session(user_id: UUID = Depends(get_user_id)):
    """Get the currently active pomodoro session for the user, if any."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/tasks/{task_id}/pomodoro", response_model=PomodoroSessionListResponse)
async def list_task_sessions(task_id: UUID, user_id: UUID = Depends(get_user_id)):
    """List all pomodoro sessions for a specific task."""
    raise HTTPException(status_code=501, detail="Not implemented")
