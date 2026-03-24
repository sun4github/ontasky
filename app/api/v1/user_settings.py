from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.common import get_user_id
from app.schemas.user_settings import UserSettingsResponse, UserSettingsUpdateRequest

router = APIRouter(prefix="/api/v1", tags=["settings"])


# ---------------------------------------------------------------------------
# User settings
# ---------------------------------------------------------------------------


@router.get("/user/settings", response_model=UserSettingsResponse)
async def get_settings(user_id: UUID = Depends(get_user_id)):
    """Get user settings (pomodoro duration, break duration, timezone, alert sound)."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.patch("/user/settings", response_model=UserSettingsResponse)
async def update_settings(
    req: UserSettingsUpdateRequest,
    user_id: UUID = Depends(get_user_id),
):
    """Update user settings. Only provided fields are updated."""
    raise HTTPException(status_code=501, detail="Not implemented")
