from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class ResponseBase(BaseModel, Generic[T]):
    status: str
    message: str
    status_code: int
    data: Optional[T] = None


class SuccessResponse(ResponseBase[T]):
    status: str = "success"
    message: str = "Request Successful"
    status_code: int = 200


class ErrorResponse(ResponseBase[T]):
    status: str = "error"
    message: str = "Something Went Wrong."
    status_code: int = 400
    error: str = ""


class AppError(Exception):
    def __init__(self, error_response: ErrorResponse[T]):
        super().__init__()
        self.error_response = error_response
