from dataclasses import dataclass
from enum import Enum
from fastapi import status


@dataclass(frozen=True)
class ErrorDetail:
    status_code: int
    message: str 
    error: str
    # data: dict | None = None

    def set_message(self, message: str) -> "ErrorDetail":
        return ErrorDetail(
            status_code=self.status_code,
            message=message,
            error=self.error,
        )
    
    # def set_data(self, data: dict[str, Any]) -> "ErrorDetail":
    #     return ErrorDetail(
    #         status_code=self.status,
    #         message=self.message,
    #         error=self.error,
    #         data=data,
    #     )


class RuntimePipelineExecutionErrors(Enum):
    NODE_NOT_FOUND_ERROR = ErrorDetail(
        status_code=status.HTTP_404_NOT_FOUND,
        message="Node with the provided key not found.",
        error="node_not_found_error",
    )
    CREDENTIALS_NOT_FOUND_ERROR = ErrorDetail(
        status_code=status.HTTP_404_NOT_FOUND,
        message="No credentials found for the requested service.",
        error="credentials_not_found_error",
    )
    PERMISSIONS_NOT_SUFFICIENT_ERROR = ErrorDetail(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="You didn't have enough permissions to perform this action.",
        error="permisssions_not_sufficient_error",
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
        error="user_not_found_when_updating_scope",
    )
    INVALID_JWT_TOKEN_ERROR = ErrorDetail(
        status_code=401,
        message="Session expired! Please re-login.",
        error="access_token_expired",
    )
    USER_NOT_FOUND_ERROR = ErrorDetail(
        status_code=404, message="Invalid access error.", error="user_not_found"
    )
    PERMISSION_DENIED_ERROR = ErrorDetail(
        status_code=400,
        message="You are not allowed to access this service.",
        error="permission_denied",
    )


class AppError(Exception):
    def __init__(self, detail: ErrorDetail, data: dict[str, str] | None = None):
        self.detail = detail
        self.data = data
