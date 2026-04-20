import uuid
from datetime import datetime, timezone, timedelta

import jwt
from loguru import logger
from typing import Literal
from fastapi import Response

from src.config import CONFIG


def _parse_expiry(raw: str) -> timedelta:
    """Convert human-friendly expiry strings to timedelta.

    Supports: 30s, 15m, 1h, 7d
    """
    raw = raw.strip().lower()
    unit = raw[-1]
    value = int(raw[:-1])
    mapping = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    if unit not in mapping:
        raise ValueError(
            f"Unsupported expiry unit '{unit}'. Use one of: {list(mapping.keys())}"
        )
    return timedelta(**{mapping[unit]: value})


ACCESS_TOKEN_EXPIRY = _parse_expiry(CONFIG.ACCESS_TOKEN_EXPIRY)
REFRESH_TOKEN_EXPIRY = _parse_expiry(CONFIG.REFRESH_TOKEN_EXPIRY)


def create_jwt_token(
    user_id: uuid.UUID,
    token_type: Literal["access", "refresh"],
    extra_claims: dict | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + (
        ACCESS_TOKEN_EXPIRY if token_type == "access" else REFRESH_TOKEN_EXPIRY
    )
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": expires_at,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, CONFIG.JWT_SECRET, algorithm=CONFIG.JWT_ALGORITHM)
    logger.debug(f"{token_type.capitalize()} token created for user {user_id}")
    return token


def verify_token(token: str, expected_type: str = "access") -> dict:
    """Decode and validate a JWT.

    Parameters
    ----------
    token : str
        The raw JWT string.
    expected_type : str
        Must match the ``type`` claim ("access" | "refresh").

    Returns
    -------
    dict
        The decoded payload.

    Raises
    ------
    jwt.ExpiredSignatureError
        Token has expired.
    jwt.InvalidTokenError
        Generic JWT validation failure.
    ValueError
        Token ``type`` claim does not match ``expected_type``.
    """
    payload = jwt.decode(
        token,
        CONFIG.JWT_SECRET,
        algorithms=[CONFIG.JWT_ALGORITHM],
    )

    if payload.get("type") != expected_type:
        raise ValueError(
            f"Invalid token type: expected '{expected_type}', "
            f"got '{payload.get('type')}'"
        )

    return payload


def set_cookies(response: Response, tokens: dict[str, str]):
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    if access_token:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=int(ACCESS_TOKEN_EXPIRY.total_seconds()),
        )
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=int(REFRESH_TOKEN_EXPIRY.total_seconds()),
        )
