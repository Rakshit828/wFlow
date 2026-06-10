from src.core.response import ErrorResponse, T
from fastapi import status


class EmptySessionTokenError(ErrorResponse[T]):
    status_code: int = status.HTTP_401_UNAUTHORIZED
    message: str = "No session token. Please login."
    error: str = "empty_session_token_error"


class InvalidSessionTokenError(ErrorResponse[T]):
    status_code: int = status.HTTP_401_UNAUTHORIZED
    message: str = "Invalid or expired session token. Re-login required."
    error: str = "invalid_session_token_error"


class SessionTokenExpiredError(ErrorResponse[T]):
    status_code: int = status.HTTP_401_UNAUTHORIZED
    message: str = "Session expired. Please relogin again."
    error: str = "session_token_expired_error"
