from src.integrations.services.Google.oauth2 import GoogleOAuthInterface
from src.integrations.services.Google.g_types import (
    GoogleAuthResponse,
    GoogleIDTokenPayload,
    GoogleIDTokenPayloadOnlyEmail,
    GoogleNewScopeResponse,
    CredentialsModel,

    GoogleApiErrorDetail,
    GoogleApiErrorResponse,
    GoogleErrorStatus,

    SERVICE_THAT_SHOULD_BE_REPLACED_BY_IN_BASE_URL
)
from src.integrations.services.Google.shared import CommonGoogleConfigModel
from src.integrations.services.Google.service_client import GoogleAPIClient
from src.integrations.services.Google.scopes import GOOGLE_SCOPES, GOOGLE_SERVICES

__all__ = [
    "GoogleOAuthInterface",
    "GoogleAuthResponse",
    "GoogleIDTokenPayload",
    "GoogleIDTokenPayloadOnlyEmail",
    "GoogleNewScopeResponse",
    "GOOGLE_SCOPES",
    "GOOGLE_SERVICES",
    "CredentialsModel",
    "GoogleAPIClient",
    "GoogleApiErrorDetail",
    "GoogleApiErrorResponse",
    "GoogleErrorStatus",
    "CommonGoogleConfigModel",
    "SERVICE_THAT_SHOULD_BE_REPLACED_BY_IN_BASE_URL"
]
