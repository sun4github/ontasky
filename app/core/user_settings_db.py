"""Async database helpers for the user_settings table. No ORM - psycopg3 only."""

from __future__ import annotations

from uuid import UUID

from psycopg.rows import dict_row

from app.core.db import get_pool

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TABLE = "public.user_settings"

_USER_SETTINGS_COLS = (
    "user_id, alert_sound, pomodoro_mins, break_mins, timezone, updated_at"
)

_UPDATABLE = {"alert_sound", "pomodoro_mins", "break_mins", "timezone"}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


async def create_user_settings(user_id: UUID, **fields: object) -> dict:
    """Create user settings and return the row.

    Accepts only updatable fields; missing values rely on DB defaults.
    Safe under races via ON CONFLICT.
    """
    safe_fields = {k: v for k, v in fields.items() if k in _UPDATABLE}

    cols = ["user_id", *safe_fields.keys()]
    values = [user_id, *safe_fields.values()]
    placeholders = ", ".join(["%s"] * len(cols))

    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                INSERT INTO {_TABLE} ({", ".join(cols)})
                VALUES ({placeholders})
                ON CONFLICT (user_id) DO NOTHING
                RETURNING {_USER_SETTINGS_COLS}
                """,
                values,
            )
            row = await cur.fetchone()
            if row is not None:
                return row

            cur = await conn.execute(
                f"SELECT {_USER_SETTINGS_COLS} FROM {_TABLE} WHERE user_id = %s",
                (user_id,),
            )
            existing = await cur.fetchone()
            return existing  # type: ignore[return-value]


async def get_user_settings(user_id: UUID) -> dict:
    """Return user settings for a user, auto-creating defaults if absent."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"SELECT {_USER_SETTINGS_COLS} FROM {_TABLE} WHERE user_id = %s",
            (user_id,),
        )
        row = await cur.fetchone()
        if row is not None:
            return row

    return await create_user_settings(user_id)


async def update_user_settings(user_id: UUID, **fields: object) -> dict:
    """Update provided settings fields and return the resulting row.

    If no valid fields are supplied, returns current settings (auto-created if
    missing). If the row is missing and valid fields are provided, creates it
    using those values plus DB defaults for omitted columns.
    """
    safe_fields = {k: v for k, v in fields.items() if k in _UPDATABLE}
    if not safe_fields:
        return await get_user_settings(user_id)

    cols = ["user_id", *safe_fields.keys()]
    values = [user_id, *safe_fields.values()]
    placeholders = ", ".join(["%s"] * len(cols))

    set_parts = [f"{col} = EXCLUDED.{col}" for col in safe_fields.keys()]
    set_parts.append("updated_at = now()")

    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                INSERT INTO {_TABLE} ({", ".join(cols)})
                VALUES ({placeholders})
                ON CONFLICT (user_id)
                DO UPDATE SET {", ".join(set_parts)}
                RETURNING {_USER_SETTINGS_COLS}
                """,
                values,
            )
            return await cur.fetchone()  # type: ignore[return-value]
