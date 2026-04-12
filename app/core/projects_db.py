"""Async database helpers for the project table. No ORM — psycopg3 only."""

from __future__ import annotations

from uuid import UUID

from psycopg.rows import dict_row

from app.core.db import get_pool

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PROJECT_COLS = "id, user_id, path, created_at, is_deleted, is_completed"

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
             AND is_deleted = false 
             AND is_completed = false 
             ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = await cur.fetchall()
        return {"items": rows, "total": len(rows)}


async def search_projects(
    user_id: UUID,
    q: str,
    limit: int = 20,
    include_completed: bool = False,
    include_deleted: bool = False,
) -> dict:
    """Search projects by leaf segment from path for a user.

    Returns ``{"items": [...], "total": <int>}``.
    """
    pool = get_pool()
    pattern = f"%{q}%"

    clauses: list[str] = []
    if not include_deleted:
        clauses.append("AND is_deleted = false")
    if not include_completed:
        clauses.append("AND is_completed = false")
    where_extra = " ".join(clauses)

    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"""
            SELECT {_PROJECT_COLS}
              FROM project
             WHERE user_id = %s
               AND split_part(path, '/', array_length(string_to_array(path, '/'), 1)) ILIKE %s
               {where_extra}
             ORDER BY created_at DESC
             LIMIT %s
            """,
            (user_id, pattern, limit),
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
            status = cur.statusmessage
            # Parse the status message to check if a row was deleted
            # Status message format is "DELETE X" where X is the number of rows
            rows_deleted = int(status.split()[1]) if status and " " in status else 0
            return rows_deleted > 0


async def soft_delete_project(project_id: UUID, user_id: UUID) -> dict | None:
    """Soft-delete a project: marks it and all its tasks as deleted, hard-deletes subtasks.

    Returns the updated project row, or None if not found.
    """
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            # Hard-delete subtasks for all tasks in this project
            await conn.execute(
                """
                DELETE FROM subtask
                 WHERE task_id IN (
                     SELECT id FROM task WHERE project_id = %s AND user_id = %s
                 )
                """,
                (project_id, user_id),
            )
            # Soft-delete all tasks in this project
            await conn.execute(
                """
                UPDATE task
                   SET is_deleted = true, updated_at = now()
                 WHERE project_id = %s AND user_id = %s
                """,
                (project_id, user_id),
            )
            # Soft-delete the project
            cur = await conn.execute(
                f"""
                UPDATE project
                   SET is_deleted = true
                 WHERE id = %s AND user_id = %s
                RETURNING {_PROJECT_COLS}
                """,
                (project_id, user_id),
            )
            return await cur.fetchone()


async def complete_project(project_id: UUID, user_id: UUID) -> dict | None:
    """Mark a project as completed and return the updated row, or None."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
             # mark all tasks in this project as completed
            await conn.execute(
                """
                UPDATE task
                   SET status = 'completed', updated_at = now()
                 WHERE project_id = %s AND user_id = %s
                """,
                (project_id, user_id),
            )
            cur = await conn.execute(
                f"""
                UPDATE project
                   SET is_completed = true
                 WHERE id = %s AND user_id = %s
                RETURNING {_PROJECT_COLS}
                """,
                (project_id, user_id),
            )
            return await cur.fetchone()


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