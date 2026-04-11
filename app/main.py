from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from fastmcp import FastMCP
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastmcp.server.providers import FileSystemProvider

from app.core.config import settings
from app.core.db import close_pool, open_pool
from app.api.v1 import assigners, pomodoro, projects, subtasks, tasks, user_settings

# Point the provider to your tools directory
mcp_provider = FileSystemProvider(Path(__file__).parent / "mcp_tools")

mcp = FastMCP("OnTaskyMCP", providers=[mcp_provider])
# Create the MCP ASGI app with path="/" since we'll mount at /mcp
mcp_app = mcp.http_app(path="/", stateless_http=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context.

    * Code before `yield` runs once when the ASGI server starts.
    * Code after `yield` runs once when the server is shutting down.
    """
    async with mcp_app.lifespan(app):  # Ensure MCP lifespan is managed
        # ---- startup ---------------------------------------------------------
        await open_pool()          # create the shared async connection pool
        # Pre-generate schema at startup so Swagger UI has docs immediately.
        app.openapi_schema = app.openapi()
        yield                     # <-- control passes to the running FastAPI app
        # ---- shutdown --------------------------------------------------------
        await close_pool()        # gracefully close the pool




app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Task management API with Pomodoro support.",
    lifespan=lifespan,
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Mount to FastAPI as before
app.mount("/mcp", mcp_app)

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


@app.get("/", include_in_schema=False)
async def docs_redirect() -> RedirectResponse:
    """Redirect root URL to Swagger UI."""
    return RedirectResponse(url="/swagger")


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Returns service liveness status."""
    return {"status": "ok"}
