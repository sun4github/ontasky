#!/usr/bin/env python3
"""
Script to generate non-expiring agent tokens for Ontasky.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from uuid import uuid4
import psycopg
from core.auth import create_access_token
from core.config import settings


def main():
    agent_id = uuid4()
    print(f"Generated agent UUID: {agent_id}")
    username = input("Enter a username for this agent (optional, press Enter to skip): ").strip() or None
    if not username:
        username = f"bot_{uuid4().hex[:8]}"
    print(f"Entered/Generated username: {username}")

    with psycopg.connect(settings.db_conninfo) as conn:
        conn.execute(
            """
            INSERT INTO app_user (id, username, user_type)
            VALUES (%s, %s, %s::user_type)
            ON CONFLICT (id) DO NOTHING
            """,
            (agent_id, username, "agent"),
        )
        conn.commit()
    print("Agent user registered in app_user.")

    token = create_access_token(
        user_id=agent_id,
        token_kind="agent",
        allow_non_expiry=True,
    )
    print(f"Agent token: {token}")


if __name__ == "__main__":
    main()