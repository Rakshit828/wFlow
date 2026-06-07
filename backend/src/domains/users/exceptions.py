from src.core.response import ErrorResponse, T
from fastapi import status

class UserNotFoundError(ErrorResponse[T]):
    status_code: int = status.HTTP_404_NOT_FOUND
    message: str = "User not found."
    error: str = "user_not_found_error"
