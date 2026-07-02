from pydantic import BaseModel, EmailStr, HttpUrl, ConfigDict, computed_field
from typing import Optional, List
from src.integrations.services.Google.scopes import (
    GOOGLE_EMAIL_ONLY_OPENID_SCOPE,
    GOOGLE_SERVICES,
    SERVICE_MAPPINGS,
    GOOGLE_SCOPES,
)
from typing import TypedDict, List
from enum import Enum
from loguru import logger

SERVICE_THAT_SHOULD_BE_REPLACED_BY_IN_BASE_URL: list[str] = ["gmail", "gsheets"]


class GoogleApiErrorDetail(TypedDict):
    message: str
    domain: str
    reason: str
    location: str
    locationType: str


class GoogleErrorStatus(str, Enum):
    PERMISSION_DENIED = "PERMISSION_DENIED"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"

    # These bottom constants are AI-Generated, not known till now
    FAILED_PRECONDITION = "FAILED_PRECONDITION"
    ABORTED = "ABORTED"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    UNIMPLEMENTED = "UNIMPLEMENTED"
    INTERNAL = "INTERNAL"
    UNAVAILABLE = "UNAVAILABLE"
    DATA_LOSS = "DATA_LOSS"
    NOT_FOUND = "NOT_FOUND"


class GoogleApiErrorResponse(TypedDict):
    code: int
    message: str
    errors: List[GoogleApiErrorDetail]
    status: GoogleErrorStatus


class GoogleIDTokenPayload(BaseModel):
    """This is the decoded id_token payload when all [openid, email, profile] are requested."""

    iss: str  # Must be https://accounts.google.com
    azp: str  # Your Client ID
    aud: str  # Your Client ID
    sub: str  # Unique Google User ID
    email: EmailStr
    email_verified: bool
    at_hash: Optional[str] = None
    name: str
    picture: Optional[HttpUrl] = None
    given_name: str
    family_name: str
    iat: int  # Issued at
    exp: int  # Expiration time


class GoogleAuthResponse(BaseModel):
    access_token: str
    expires_in: int

    refresh_token: Optional[str] = None
    scope: str
    token_type: str
    decoded_id_token: GoogleIDTokenPayload

    @computed_field()
    @property
    def scopes(self) -> list[str]:
        return self.scope.split(" ")

    model_config = ConfigDict(extra="ignore")


class GoogleIDTokenPayloadOnlyEmail(BaseModel):
    """This is the decoded id_token payload when all [openid, email] are requested."""

    iss: str  # Must be https://accounts.google.com
    azp: str  # Your Client ID
    aud: str  # Your Client ID
    sub: str  # Unique Google User ID
    email: EmailStr
    email_verified: bool
    at_hash: Optional[str] = None
    iat: int  # Issued at
    exp: int  # Expiration time


class GoogleNewScopeResponse(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: Optional[str] = None
    refresh_token_expires_in: int
    scope: str
    token_type: str
    decoded_id_token: GoogleIDTokenPayloadOnlyEmail

    @computed_field()
    @property
    def scopes(self) -> list[str]:
        scopes_list = self.scope.split(" ")
        return scopes_list

    @computed_field
    @property
    def service(self) -> str:
        """Identifies the service from the scopes."""
        logger.info(f"Scope: {self.scope}, Scopes: {self.scopes}")
        for scope in GOOGLE_EMAIL_ONLY_OPENID_SCOPE:
            if scope in self.scope:
                self.scope.replace(scope, "")
            elif GOOGLE_SCOPES[scope] in self.scope:
                self.scope.replace(GOOGLE_SCOPES[scope], "")

        self.scope = self.scope.strip()

        for service in GOOGLE_SERVICES:
            if service in self.scope:
                if service in SERVICE_MAPPINGS:
                    return SERVICE_MAPPINGS[service]
                return service
