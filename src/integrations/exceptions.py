from src.utils.exceptions import ErrorDetail
from fastapi import status
from enum import Enum

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
