"""Async database helpers for assigner credentials and grants. No ORM."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from psycopg.rows import dict_row

from app.core.db import get_pool

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ASSIGNER_CREDENTIAL_COLS = (
    "id, assigner_user_id, key_hash, label, created_at, expires_at, "
    "revoked_at, last_used_at"
)

_TASK_ASSIGNER_GRANT_COLS = (
    "id, user_id, assigner_user_id, permissions, expires_at, granted_by_user_id, "
    "created_at, revoked_at"
)


# ---------------------------------------------------------------------------
# Credential functions
# ---------------------------------------------------------------------------


async def create_assigner_credential(
    assigner_user_id: UUID,
    key_hash: str,
    label: str,
    expires_at: datetime | None = None,
) -> dict:
    """Insert a new assigner credential and return the created row."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                INSERT INTO assigner_credential (assigner_user_id, key_hash, label, expires_at)
                VALUES (%s, %s, %s, %s)
                RETURNING {_ASSIGNER_CREDENTIAL_COLS}
                """,
                (assigner_user_id, key_hash, label, expires_at),
            )
            return await cur.fetchone()  # type: ignore[return-value]


async def list_active_assigner_credentials(assigner_user_id: UUID) -> dict:
    """Return active (not revoked and not expired) credentials for an assigner.

    Returns ``{"items": [...], "total": <int>}``.
    """
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"""
            SELECT {_ASSIGNER_CREDENTIAL_COLS}
              FROM assigner_credential
             WHERE assigner_user_id = %s
               AND revoked_at IS NULL
               AND (expires_at IS NULL OR expires_at > now())
             ORDER BY created_at DESC
            """,
            (assigner_user_id,),
        )
        rows = await cur.fetchall()
        return {"items": rows, "total": len(rows)}


async def get_assigner_credential(
    credential_id: UUID,
    assigner_user_id: UUID,
) -> dict | None:
    """Fetch a credential by id scoped to assigner_user_id, or None."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"""
            SELECT {_ASSIGNER_CREDENTIAL_COLS}
              FROM assigner_credential
             WHERE id = %s AND assigner_user_id = %s
            """,
            (credential_id, assigner_user_id),
        )
        return await cur.fetchone()


async def revoke_assigner_credential(
    credential_id: UUID,
    assigner_user_id: UUID,
) -> dict | None:
    """Soft-revoke a credential and return the updated row, or None."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                UPDATE assigner_credential
                   SET revoked_at = now()
                 WHERE id = %s AND assigner_user_id = %s AND revoked_at IS NULL
                RETURNING {_ASSIGNER_CREDENTIAL_COLS}
                """,
                (credential_id, assigner_user_id),
            )
            return await cur.fetchone()


# ---------------------------------------------------------------------------
# Grant functions
# ---------------------------------------------------------------------------


async def create_task_assigner_grant(
    user_id: UUID,
    assigner_user_id: UUID,
    granted_by_user_id: UUID,
    permissions: dict[str, object],
    expires_at: datetime | None = None,
) -> dict:
    """Create or reactivate a grant and return the resulting row.

    Uses ``ON CONFLICT (user_id, assigner_user_id)`` to upsert and clears
    ``revoked_at`` when a previously revoked grant is re-granted.
    """
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                INSERT INTO task_assigner_grant (
                    user_id,
                    assigner_user_id,
                    permissions,
                    expires_at,
                    granted_by_user_id
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, assigner_user_id)
                DO UPDATE
                   SET permissions = EXCLUDED.permissions,
                       expires_at = EXCLUDED.expires_at,
                       granted_by_user_id = EXCLUDED.granted_by_user_id,
                       revoked_at = NULL
                RETURNING {_TASK_ASSIGNER_GRANT_COLS}
                """,
                (user_id, assigner_user_id, permissions, expires_at, granted_by_user_id),
            )
            return await cur.fetchone()  # type: ignore[return-value]


async def list_active_task_assigner_grants(user_id: UUID) -> dict:
    """Return active (not revoked and not expired) grants for a user.

    Returns ``{"items": [...], "total": <int>}``.
    """
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"""
            SELECT {_TASK_ASSIGNER_GRANT_COLS}
              FROM task_assigner_grant
             WHERE user_id = %s
               AND revoked_at IS NULL
               AND (expires_at IS NULL OR expires_at > now())
             ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = await cur.fetchall()
        return {"items": rows, "total": len(rows)}


async def get_task_assigner_grant(
    user_id: UUID,
    assigner_user_id: UUID,
) -> dict | None:
    """Fetch a grant scoped to (user_id, assigner_user_id), or None."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        cur = await conn.execute(
            f"""
            SELECT {_TASK_ASSIGNER_GRANT_COLS}
              FROM task_assigner_grant
             WHERE user_id = %s AND assigner_user_id = %s
            """,
            (user_id, assigner_user_id),
        )
        return await cur.fetchone()


async def revoke_task_assigner_grant(
    user_id: UUID,
    assigner_user_id: UUID,
) -> dict | None:
    """Soft-revoke a grant and return the updated row, or None."""
    pool = get_pool()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        async with conn.transaction():
            cur = await conn.execute(
                f"""
                UPDATE task_assigner_grant
                   SET revoked_at = now()
                 WHERE user_id = %s AND assigner_user_id = %s AND revoked_at IS NULL
                RETURNING {_TASK_ASSIGNER_GRANT_COLS}
                """,
                (user_id, assigner_user_id),
            )
            return await cur.fetchone()