from dataclasses import dataclass
from enum import Enum
from typing import Any

@dataclass(frozen=True)
class ErrorDetail:
    status_code: int
    message: int
    error: str


class AuthErrors(Enum):
    ACCESS_TOKEN_EXPIRED_ERROR = ErrorDetail(
        status_code=401,
        message="Session expired! Please re-login.",
        error="access_token_expired",
    )
    USER_NOT_FOUND_WHEN_UPDATING_SCOPE = ErrorDetail(
        status_code=404,
        message="User not found",
        error="user_not_found_when_updating_scope"
    )


class AppError(Exception):
    def __init__(self, detail: ErrorDetail, data: dict[str, Any] | None = None):
        self.detail = detail
        self.data = data