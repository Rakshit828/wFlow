from src.core.response import ErrorResponse, T
from fastapi import status


class InvalidJwtTokenError(ErrorResponse[T]):
    status_code: int = status.HTTP_401_UNAUTHORIZED
    message: str = "Invalid JWT token."
    error: str = "invalid_jwt_token_error"


class JwtTokenExpiredError(ErrorResponse[T]):
    status_code: int = status.HTTP_401_UNAUTHORIZED
    message: str = "Session expired. Please relogin again."
    error: str = "jwt_token_expired_error"
