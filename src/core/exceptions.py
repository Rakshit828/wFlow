from dataclasses import dataclass
from enum import Enum
from typing import Any
from fastapi import status

@dataclass(frozen=True)
class ErrorDetail:
    status_code: int
    message: int
    error: str


class GeneralIntegrationErrors(Enum):
    REQUESTED_MULTIPLE_SERVICE_SCOPE_ERROR = ErrorDetail(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Cannot request scopes of multiple service.",
        error="requested_multiple_service_scope_error"
    )
    INVALID_SERVICE_REQUESTED_ERROR = ErrorDetail(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Cannot find the service you requested for.",
        error="invalid_service_requested_error"
    )
    

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
    INVALID_JWT_TOKEN_ERROR = ErrorDetail(
        status_code=401,
        message="Session expired! Please re-login.",
        error="access_token_expired",
    )
    USER_NOT_FOUND_ERROR = ErrorDetail(
        status_code=404,
        message="Invalid access error.",
        error="user_not_found"
    )
    PERMISSION_DENIED_ERROR = ErrorDetail(
        status_code=400,
        message="You are not allowed to access this service.",
        error="permission_denied"
    )
    


class AppError(Exception):
    def __init__(self, detail: ErrorDetail, data: dict[str, Any] | None = None):
        self.detail = detail
        self.data = data