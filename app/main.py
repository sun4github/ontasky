from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import close_pool, open_pool
from app.api.v1 import assigners, pomodoro, projects, subtasks, tasks, user_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context.

    * Code before `yield` runs once when the ASGI server starts.
    * Code after `yield` runs once when the server is shutting down.
    """
    # ---- startup ---------------------------------------------------------
    await open_pool()          # create the shared async connection pool
    yield                     # <-- control passes to the running FastAPI app
    # ---- shutdown --------------------------------------------------------
    await close_pool()        # gracefully close the pool


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Task management API with Pomodoro support.",
     lifespan=lifespan
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
app.include_router(assigners.router)


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Returns service liveness status."""
    return {"status": "ok"}
