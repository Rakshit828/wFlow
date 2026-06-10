from src.config import CONFIG
from datetime import timedelta
from fastapi import Response
from loguru import logger
import time
import functools


def timer(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} executed in {end - start:.6f} seconds")
        return result

    return wrapper


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


def set_cookie(response: Response, key: str, value: str, expiry: timedelta):
    """Set JWT tokens as HTTP-only cookies in the response."""
    response.set_cookie(
        key=key,
        value=value,
        max_age=int(expiry.total_seconds()),
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )
    # httponly=True,
    # secure=True,
    # samesite="none",
