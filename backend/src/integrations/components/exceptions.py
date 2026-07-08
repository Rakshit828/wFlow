from typing import Any, Dict, Optional


class BaseError(Exception):
    """Base exception for all errors."""

    def __init__(self, message: str, meta: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.meta = meta or {}

class DatabaseError(BaseError):
    pass 

class ApiConnectionError(BaseError):
    """Raised when establishing connection to service client is not happening."""


class AuthenticationError(BaseError):
    """Raised when credentials are invalid or expired."""
    pass


class AuthorizationError(BaseError):
    """Raised when the user lacks required permissions for the resource."""
    pass


class RateLimitingError(BaseError):
    """Raised when the service API rate limit is exceeded."""
    pass


class ServiceSpecificError(BaseError):
    """Raised for errors unique to a provider (e.g., Gmail, Google Drive)."""

    def __init__(
        self, message: str, service_name: str, meta: Optional[Dict[str, Any]] = None
    ):
        meta = meta or {}
        meta["service"] = service_name
        super().__init__(message, meta=meta)
