from .response import AppError
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request
from loguru import logger


def app_error_handler(request: Request, exc: AppError):
    logger.error(
        f"Error occurred: {exc.error_response.error}, "
        f"Message: {exc.error_response.message}, "
        f"Status: {exc.error_response.status_code}, "
        f"Path: {request.url.path}"
    )
    err_response = exc.error_response.model_dump()
    err_response.pop("error")
    return JSONResponse(
        status_code=exc.error_response.status_code,  # This status code is of the JSONResponse itself
        content=err_response,  # Our response resides here
    )


def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Convert Pydantic errors into your structure
    raise exc
    error_msg = ""
    missing_fields = ""
    for error in exc.errors():
        if error["type"] == "missing":
            missing_fields = missing_fields + error["loc"][1] + ", "
        elif error["type"] == "json_invalid":
            error_msg = "Invalid Json Structure."

    if missing_fields:
        error_msg = f"Missing {missing_fields}"

    logger.error(
        f"Error occurred: {[error['type'] for error in exc.errors()]}, "
        f"Message: {error_msg if error_msg else exc.errors()}, "
        f"Status: {400}, "
        f"Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "status_code": 400,
            "error": "validation_error",
            "message": error_msg,
        },
    )
