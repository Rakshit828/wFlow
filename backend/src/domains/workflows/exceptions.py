from src.core.response import ErrorResponse, T
from fastapi import status

class WorkflowNotFoundError(ErrorResponse[T]):
    status_code: int = status.HTTP_404_NOT_FOUND
    message: str = "Workflow not found."
    error: str = "workflow_not_found_error"