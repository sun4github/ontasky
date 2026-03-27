"""Async database helpers for the subtask table. No ORM — psycopg3 only."""

from __future__ import annotations

from uuid import UUID

from psycopg.rows import dict_row

from app.core.db import get_pool

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SUBTASK_COLS = (
    "id, task_id, title, is_completed, sort_order, created_at, completed_at"
)

# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


async def create_subtask(
    task_id: UUID,
    title: str,
    sort_order: int,
) -> dict:
    """Insert a new subtask and return the created row as a dict."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            row = await conn.execute(
                """
                INSERT INTO subtask (task_id, title, sort_order)
                VALUES (%s, %s, %s)
                RETURNING """ + _SUBTASK_COLS,
                (task_id, title, sort_order),
            )
            return await row.fetchone()  # type: ignore[return-value]


async def list_subtasks(
    task_id: UUID,
) -> dict:
    """Return subtasks for a task, ordered by sort_order.

    Returns ``{"items": [...], "total": <int>}``.
    """
    pool = get_pool()

    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"""
            SELECT {_SUBTASK_COLS}
              FROM subtask
             WHERE task_id = %s
             ORDER BY sort_order ASC
            """,
            (task_id,),
        )
        rows = await cur.fetchall()
        return {"items": rows, "total": len(rows)}


async def get_subtask(subtask_id: UUID, task_id: UUID) -> dict | None:
    """Fetch a single subtask by id scoped to the task, or None."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"SELECT {_SUBTASK_COLS} FROM subtask WHERE id = %s AND task_id = %s",
            (subtask_id, task_id),
        )
        return await cur.fetchone()


async def update_subtask(subtask_id: UUID, task_id: UUID, **fields: object) -> dict | None:
    """Update only the supplied columns and return the updated row.

    Returns ``None`` when no matching subtask exists.
    """
    set_parts: list[str] = []
    params: list[object] = []
    
    if "title" in fields:
        set_parts.append("title = %s")
        params.append(fields["title"])
    
    if "is_completed" in fields:
        set_parts.append("is_completed = %s")
        params.append(fields["is_completed"])
        if fields["is_completed"]:
            set_parts.append("completed_at = now()")
        else:
            set_parts.append("completed_at = NULL")
    
    if not set_parts:
        # Nothing to update — just return current state.
        return await get_subtask(subtask_id, task_id)

    params.extend([subtask_id, task_id])
    set_parts.append("updated_at = now()")
    
    set_clause = ", ".join(set_parts)

    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                UPDATE subtask
                   SET {set_clause}
                 WHERE id = %s AND task_id = %s
                RETURNING {_SUBTASK_COLS}
                """,
                params,
            )
            return await cur.fetchone()


async def complete_subtask(subtask_id: UUID, task_id: UUID) -> dict | None:
    """Mark a subtask as completed and return the updated row, or None."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                UPDATE subtask
                   SET is_completed = true, completed_at = now()
                 WHERE id = %s AND task_id = %s
                RETURNING {_SUBTASK_COLS}
                """,
                (subtask_id, task_id),
            )
            return await cur.fetchone()


async def reorder_subtasks(task_id: UUID, subtask_ids: list[UUID]) -> dict:
    """Reorder subtasks by updating their sort_order based on the provided IDs.

    Returns ``{"items": [...], "total": <int>}``.
    """
    pool = get_pool()
    
    if not subtask_ids:
        return {"items": [], "total": 0}
    
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            # Update sort_order for each subtask based on its position in the list
            for index, subtask_id in enumerate(subtask_ids):
                await conn.execute(
                    """
                    UPDATE subtask
                       SET sort_order = %s
                     WHERE id = %s AND task_id = %s
                    """,
                    (index, subtask_id, task_id),
                )
            
            # Fetch all reordered subtasks
            cur = await conn.execute(
                f"""
                SELECT {_SUBTASK_COLS}
                  FROM subtask
                 WHERE task_id = %s
                 ORDER BY sort_order ASC
                """,
                (task_id,),
            )
            rows = await cur.fetchall()
            return {"items": rows, "total": len(rows)}


async def delete_subtask(subtask_id: UUID, task_id: UUID) -> bool:
    """Delete a subtask. Returns True if a row was removed."""
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.transaction():
            cur = await conn.execute(
                "DELETE FROM subtask WHERE id = %s AND task_id = %s",
                (subtask_id, task_id),
            )
            return cur.rowcount > 0
