from pydantic import BaseModel, EmailStr, HttpUrl, Field, ConfigDict, computed_field
from typing import Optional, List
from src.integrations.googlecould.scopes import GOOGLE_EMAIL_ONLY_OPENID_SCOPE, GOOGLE_SERVICES


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
    refresh_expires_in: int
    scope: str
    token_type: str
    decoded_id_token: GoogleIDTokenPayloadOnlyEmail

    @computed_field()
    @property
    def scopes(self) -> list[str]:
        return self.scope.split(" ")

    @computed_field
    @property
    def service(self) -> str:
        scope_str = self.scope.replace(GOOGLE_EMAIL_ONLY_OPENID_SCOPE, "")
        for service in GOOGLE_SERVICES:
            if service in scope_str:
                return service
