#!/usr/bin/env python3
"""
Script to generate non-expiring agent tokens for Ontasky.
"""

import sys
import os

# Add the app directory to the Python path so we can import from app.core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from uuid import uuid4
from core.auth import create_access_token


def main():
    # Generate a new UUID for the agent
    agent_id = uuid4()
    print(f"Generated agent UUID: {agent_id}")
    
    # Create a non-expiring agent token
    # For non-expiring tokens, we need:
    # 1. token_kind != "human" (using "agent")
    # 2. allow_non_expiry = True
    token = create_access_token(
        user_id=agent_id,
        token_kind="agent",
        allow_non_expiry=True
    )
    print(f"Agent token: {token}")


if __name__ == "__main__":
    main()