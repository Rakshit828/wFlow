from datetime import timedelta
from fastapi import Response
import time
from typing import Callable, TypeVar
from collections.abc import Awaitable, Callable
from typing import Any
import functools

from src.db.postgres.main import AsyncSessionLocal

R = TypeVar("R")


async def wrap_in_session(
    func: Callable[..., Awaitable[R]], *args: Any, **kwargs: Any
) -> R:
    if "session" in kwargs:
        raise ValueError("Session should not be provided.")
    async with AsyncSessionLocal() as session:
        kwargs["session"] = session
        return await func(*args, **kwargs)


async def wrap_in_transaction(
    func: Callable[..., Awaitable[Any]],
    *args: tuple[Any],
    **kwargs: dict[str, Any],
) -> Any:
    if "session" in kwargs:
        raise ValueError("Session should not be provided.")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            return await func(*args, **kwargs, session=session)


def timer(func: Callable[..., Any]):
    @functools.wraps(func)
    async def wrapper(*args: tuple[Any], **kwargs: dict[str, Any]):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} executed in {end - start:.6f} seconds")
        return result

    return wrapper


def parse_expiry(raw: str) -> timedelta:
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
