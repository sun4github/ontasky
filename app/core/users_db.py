"""Async database helpers for the app_user table. No ORM — psycopg3 only."""

from __future__ import annotations

from uuid import UUID

from app.core.db import get_pool


async def upsert_app_user(user_id: UUID, username: str | None = None, user_type: str = "human") -> None:
    """Ensure an app_user row exists for user_id. Idempotent via ON CONFLICT."""
    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO app_user (id, username, user_type)
            VALUES (%s, %s, %s::user_type)
            ON CONFLICT (id) DO NOTHING
            """,
            (user_id, username, user_type),
        )