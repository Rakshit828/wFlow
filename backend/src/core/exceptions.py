from fastapi import status
from .response import ErrorResponse, T


class UnexpectedDatabaseError(ErrorResponse[T]):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Internal Server error."
    error: str = "unexpected_db_error"

class UnexpectedServerError(ErrorResponse[T]):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Internal Server error."
    error: str = "unexpected_server_error"

