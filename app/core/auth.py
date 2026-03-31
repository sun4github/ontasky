from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt

from app.core.config import settings


class AuthTokenError(Exception):
    """Raised when an access token is missing, malformed, or invalid."""


def create_access_token(
    user_id: UUID,
    username: str | None = None,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
    allow_non_expiry: bool = False,
    token_kind: str = "human"
) -> str:
    now = datetime.now(timezone.utc)
    expire_delta = expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = dict(extra_claims or {})
    payload["sub"] = str(user_id)
    if username:
        payload["username"] = username
    payload["iat"] = now
    payload["token_kind"] = token_kind
    if not (
        allow_non_expiry
        and token_kind != "human"
        and settings.JWT_ALLOW_NON_EXPIRING_AGENT_TOKENS
    ):
        payload["exp"] = now + expire_delta
    if settings.JWT_AUDIENCE:
        payload["aud"] = settings.JWT_AUDIENCE
    if settings.JWT_ISSUER:
        payload["iss"] = settings.JWT_ISSUER

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    decode_kwargs: dict[str, Any] = {
        "key": settings.JWT_SECRET_KEY,
        "algorithms": [settings.JWT_ALGORITHM],
    }
    if settings.JWT_AUDIENCE:
        decode_kwargs["audience"] = settings.JWT_AUDIENCE
    if settings.JWT_ISSUER:
        decode_kwargs["issuer"] = settings.JWT_ISSUER

    preflight_options = {
        "verify_exp": False,
        "verify_aud": bool(settings.JWT_AUDIENCE),
        "verify_iss": bool(settings.JWT_ISSUER),
    }

    try:
        preview = jwt.decode(token, options=preflight_options, **decode_kwargs)
    except jwt.PyJWTError as exc:
        raise AuthTokenError("Invalid access token") from exc

    if not isinstance(preview, dict):
        raise AuthTokenError("Invalid access token payload")

    token_kind = preview.get("token_kind", "human")
    exp_claim = preview.get("exp")

    if exp_claim is None:
        if token_kind == "human":
            raise AuthTokenError("Token expiry is required for human tokens")
        if not settings.JWT_ALLOW_NON_EXPIRING_AGENT_TOKENS:
            raise AuthTokenError("Non-expiring tokens are not allowed")
        return preview

    strict_options = {
        "verify_exp": True,
        "verify_aud": bool(settings.JWT_AUDIENCE),
        "verify_iss": bool(settings.JWT_ISSUER),
    }

    try:
        decoded = jwt.decode(token, options=strict_options, **decode_kwargs)
    except jwt.PyJWTError as exc:
        raise AuthTokenError("Invalid access token") from exc

    if not isinstance(decoded, dict):
        raise AuthTokenError("Invalid access token payload")

    return decoded