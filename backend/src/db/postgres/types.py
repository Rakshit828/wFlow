from typing import TypedDict
from datetime import datetime


class OAuth2CredentialsDict(TypedDict):
    access_token: str
    refresh_token: str | None
    access_token_expiry: datetime
    refresh_token_expiry: datetime | None = None
