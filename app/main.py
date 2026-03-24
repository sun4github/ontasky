from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import tasks, subtasks, projects, pomodoro, user_settings

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Task management API with Pomodoro support.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(subtasks.router)
app.include_router(projects.router)
app.include_router(pomodoro.router)
app.include_router(user_settings.router)


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Returns service liveness status."""
    return {"status": "ok"}
