from src.core.response import ErrorResponse, T
from fastapi import status


class WorkflowNotFoundError(ErrorResponse[T]):
    status_code: int = status.HTTP_404_NOT_FOUND
    message: str = "Workflow not found."
    error: str = "workflow_not_found_error"


class WorkflowAlreadyStarredError(ErrorResponse[T]):
    status_code: int = status.HTTP_400_BAD_REQUEST
    message: str = "Workflow already starred by user."
    error: str = "workflow_already_starred_error"


class CannotAccessPrivateWorkflowError(ErrorResponse[T]):
    status_code: int = status.HTTP_403_FORBIDDEN,
    message: str = "Your cannot access private workflow created by others."
    error: str = "cannot_access_private_workflow_error"