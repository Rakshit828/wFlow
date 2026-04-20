from pydantic import BaseModel, EmailStr, HttpUrl, Field, ConfigDict
from typing import Optional, List


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
    scopes: str
    token_type: str
    decoded_id_token: GoogleIDTokenPayload

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
    scopes: str
    token_type: str

    decoded_id_token: GoogleIDTokenPayloadOnlyEmail