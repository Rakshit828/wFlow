from src.core.response import ErrorResponse, T
from fastapi import status


class InvalidServiceRequestedError(ErrorResponse[T]):
    status_code: int = (status.HTTP_400_BAD_REQUEST,)
    message: str = "Cannot find the service you requested for."
    error: str = "invalid_service_requested_error"


class RequestedMultipleServicesScopesError(ErrorResponse[T]):
    status_code: int = status.HTTP_400_BAD_REQUEST
    message: str = "Cannot request scopes of multiple service."
    error: str = "requested_multiple_service_scope_error"


class UserNotFoundWhenUpdatingScopesError(ErrorResponse[T]):
    status_code: int = 404
    message: str = "User not found"
    error: str = "user_not_found_when_updating_scopes_error"
