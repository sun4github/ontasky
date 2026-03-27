"""Async database helpers for the project table. No ORM — psycopg3 only."""

from __future__ import annotations

from uuid import UUID

from psycopg.rows import dict_row

from app.core.db import get_pool

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PROJECT_COLS = "id, user_id, path, created_at"

_TASK_COLS = (
    "id, user_id, project_id, title, note, status, pomodoro_count, "
    "due_on, repeat_every, repeat_unit, extra, created_at, updated_at, "
    "completed_at, started_at, created_by_user_id"
)

# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


async def create_project(user_id: UUID, path: str) -> dict:
    """Insert a new project and return the created row as a dict."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            row = await conn.execute(
                f"""
                INSERT INTO project (user_id, path)
                VALUES (%s, %s)
                RETURNING {_PROJECT_COLS}
                """,
                (user_id, path),
            )
            return await row.fetchone()  # type: ignore[return-value]


async def list_projects(user_id: UUID) -> dict:
    """Return projects for a user.

    Returns ``{"items": [...], "total": <int>}``.
    """
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"""
            SELECT {_PROJECT_COLS}
              FROM project
             WHERE user_id = %s
             ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = await cur.fetchall()
        return {"items": rows, "total": len(rows)}


async def get_project(project_id: UUID, user_id: UUID) -> dict | None:
    """Fetch a single project by id scoped to the user, or None."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"SELECT {_PROJECT_COLS} FROM project WHERE id = %s AND user_id = %s",
            (project_id, user_id),
        )
        return await cur.fetchone()


async def update_project(project_id: UUID, user_id: UUID, path: str) -> dict | None:
    """Update the project path and return the updated row.

    Returns ``None`` when no matching project exists.
    """
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                UPDATE project
                   SET path = %s
                 WHERE id = %s AND user_id = %s
                RETURNING {_PROJECT_COLS}
                """,
                (path, project_id, user_id),
            )
            return await cur.fetchone()


async def delete_project(project_id: UUID, user_id: UUID) -> bool:
    """Delete a project and nullify references in tasks.

    Returns True if a project was deleted, False otherwise.
    """
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            # First nullify project_id in tasks
            await conn.execute(
                """
                UPDATE task
                   SET project_id = NULL
                 WHERE project_id = %s AND user_id = %s
                """,
                (project_id, user_id),
            )
            
            # Then delete the project
            cur = await conn.execute(
                """
                DELETE FROM project
                 WHERE id = %s AND user_id = %s
                """,
                (project_id, user_id),
            )
            status = await cur.statusmessage()
            # Parse the status message to check if a row was deleted
            # Status message format is "DELETE X" where X is the number of rows
            rows_deleted = int(status.split()[1]) if status and " " in status else 0
            return rows_deleted > 0


async def list_tasks_for_project(project_id: UUID, user_id: UUID) -> dict:
    """Return tasks for a project, using the same column list as tasks_db.py.

    Returns ``{"items": [...], "total": <int>}``.
    """
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"""
            SELECT {_TASK_COLS}
              FROM task
             WHERE project_id = %s AND user_id = %s
             ORDER BY created_at DESC
            """,
            (project_id, user_id),
        )
        rows = await cur.fetchall()
        return {"items": rows, "total": len(rows)}