"""Async database helpers for the task table. No ORM — psycopg3 only."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from psycopg.rows import dict_row

from app.core.db import get_pool

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TASK_COLS = (
    "id, user_id, project_id, title, note, status, pomodoro_count, "
    "due_on, repeat_every, repeat_unit, extra, created_at, updated_at, "
    "completed_at, started_at, created_by_user_id"
)

_UPDATABLE = {"title", "project_id", "note", "due_on", "repeat_every", "repeat_unit"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DUE_FILTERS: dict[str, str] = {
    "today": "AND due_on = CURRENT_DATE",
    "tomorrow": "AND due_on = CURRENT_DATE + 1",
    "this_week": "AND due_on BETWEEN CURRENT_DATE AND (CURRENT_DATE + interval '6 days')::date",
    "someday": "AND due_on IS NULL",
    "overdue": "AND due_on <= CURRENT_DATE",
}

# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


async def create_task(
    user_id: UUID,
    title: str,
    project_id: UUID | None = None,
    note: str | None = None,
    due_on: date | None = None,
    repeat_every: int | None = None,
    repeat_unit: str | None = None,
    created_by_user_id: UUID | None = None,
) -> dict:
    """Insert a new task and return the created row as a dict."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            row = await conn.execute(
                f"""
                INSERT INTO task (user_id, title, project_id, note, due_on,
                                  repeat_every, repeat_unit, created_by_user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING {_TASK_COLS}
                """,
                (
                    user_id,
                    title,
                    project_id,
                    note,
                    due_on,
                    repeat_every,
                    repeat_unit,
                    created_by_user_id,
                ),
            )
            return await row.fetchone()  # type: ignore[return-value]


async def list_tasks(
    user_id: UUID,
    due: str | None = None,
    project_id: UUID | None = None,
    status: str | None = None,
) -> dict:
    """Return tasks matching the given filters.

    Returns ``{"items": [...], "total": <int>}``.
    """
    pool = get_pool()

    clauses: list[str] = []
    params: list[object] = [user_id]

    if status is not None:
        clauses.append("AND status = %s")
        params.append(status)

    if project_id is not None:
        clauses.append("AND project_id = %s")
        params.append(project_id)

    if due is not None and due in _DUE_FILTERS:
        clauses.append(_DUE_FILTERS[due])

    where_extra = " ".join(clauses)

    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"""
            SELECT {_TASK_COLS}
              FROM task
             WHERE user_id = %s {where_extra}
             ORDER BY created_at DESC
            """,
            params,
        )
        rows = await cur.fetchall()
        return {"items": rows, "total": len(rows)}


async def search_tasks(user_id: UUID, q: str, limit: int = 20) -> dict:
    """Search tasks by title for a user.

    Returns ``{"items": [...], "total": <int>}``.
    """
    pool = get_pool()
    pattern = f"%{q}%"

    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"""
            SELECT {_TASK_COLS}
              FROM task
             WHERE user_id = %s
               AND title ILIKE %s
             ORDER BY created_at DESC
             LIMIT %s
            """,
            (user_id, pattern, limit),
        )
        rows = await cur.fetchall()
        return {"items": rows, "total": len(rows)}


async def get_task(task_id: UUID, user_id: UUID) -> dict | None:
    """Fetch a single task by id scoped to the user, or None."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"SELECT {_TASK_COLS} FROM task WHERE id = %s AND user_id = %s",
            (task_id, user_id),
        )
        return await cur.fetchone()


async def update_task(task_id: UUID, user_id: UUID, **fields: object) -> dict | None:
    """Update only the supplied columns and return the updated row.

    Only keys present in ``_UPDATABLE`` are accepted; others are silently
    ignored.  Returns ``None`` when no matching task exists.
    """
    safe_fields = {k: v for k, v in fields.items() if k in _UPDATABLE}
    if not safe_fields:
        # Nothing to update — just return current state.
        return await get_task(task_id, user_id)

    set_parts: list[str] = []
    params: list[object] = []
    for col, val in safe_fields.items():
        set_parts.append(f"{col} = %s")
        params.append(val)

    set_parts.append("updated_at = now()")
    params.extend([task_id, user_id])

    set_clause = ", ".join(set_parts)

    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                UPDATE task
                   SET {set_clause}
                 WHERE id = %s AND user_id = %s
                RETURNING {_TASK_COLS}
                """,
                params,
            )
            return await cur.fetchone()


async def complete_task(task_id: UUID, user_id: UUID) -> dict | None:
    """Mark a task as completed and return the updated row, or None."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                UPDATE task
                   SET status = 'completed', completed_at = now(), updated_at = now()
                 WHERE id = %s AND user_id = %s
                RETURNING {_TASK_COLS}
                """,
                (task_id, user_id),
            )
            return await cur.fetchone()


async def reopen_task(task_id: UUID, user_id: UUID) -> dict | None:
    """Re-open a completed task (set pending, clear completed_at)."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                UPDATE task
                   SET status = 'pending', completed_at = NULL, updated_at = now()
                 WHERE id = %s AND user_id = %s
                RETURNING {_TASK_COLS}
                """,
                (task_id, user_id),
            )
            return await cur.fetchone()


async def delete_task(task_id: UUID, user_id: UUID) -> bool:
    """Delete a task. Returns True if a row was removed."""
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.transaction():
            cur = await conn.execute(
                "DELETE FROM task WHERE id = %s AND user_id = %s",
                (task_id, user_id),
            )
            return cur.rowcount > 0
