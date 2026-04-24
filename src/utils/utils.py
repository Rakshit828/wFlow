from src.config import CONFIG
from datetime import timedelta
from fastapi import Response


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


def set_cookies(response: Response, tokens: dict[str, str]):
    """Set JWT tokens as HTTP-only cookies in the response."""
    
    # Set access token cookie
    if "access_token" in tokens:
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            max_age=int(ACCESS_TOKEN_EXPIRY.total_seconds()),
            httponly=True,
            secure=CONFIG.ENVIRONMENT == "production",
            samesite="none",
            path="/",
        )
    
    # Set refresh token cookie if present
    if "refresh_token" in tokens:
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            max_age=int(REFRESH_TOKEN_EXPIRY.total_seconds()),
            httponly=True,
            secure=CONFIG.ENVIRONMENT == "production",
            samesite="none",
            path="/",
        )