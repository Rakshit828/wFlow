from beanie import Document, Indexed, Link, before_event, Update, Insert
from pydantic import EmailStr, Field, ConfigDict
from typing import Optional, List, Annotated
from datetime import datetime, timezone


class Users(Document):
    email: Annotated[EmailStr, Indexed(unique=True)]
    full_name: Optional[str] = None
    username: Annotated[Optional[str], Indexed(unique=True)] = None

    is_email_verified: bool = False
    avatar_url: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


    model_config = ConfigDict(
        name = "users"
    )
    
    
    @before_event(Update)
    def set_update(self):
        self.updated_at = datetime.now(tz=timezone.utc)



class AppIntegrations(Document):
    user: Annotated[Link[Users], Indexed()]

    provider: Annotated[str, Indexed()]
    service: Annotated[str, Indexed()]
    scopes: List[str] = []

    access_token_enc: str
    access_token_expiry: datetime

    refresh_token_enc: Optional[str] = None
    refresh_token_expiry: Optional[datetime] = None

    metadata: dict | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        name = "app_integrations",
        indexes = [
            [("user", 1), ("provider", 1), ("service", 1)],
        ]
    )

    
    @before_event(Update)
    def set_update(self):
        self.updated_at = datetime.now(tz=timezone.utc)


class OAuthAccounts(Document):
    user: Annotated[Link[Users], Indexed()]

    provider: Annotated[str, Indexed()]
    provider_email: EmailStr
    provider_sub_id: str

    is_email_verified: bool = False
    scopes: List[str] = []

    access_token_enc: str
    access_token_expiry: datetime

    refresh_token_enc: Optional[str] = None
    refresh_token_expiry: Optional[datetime] = None

    created_at: datetime = Field(default_factory=lambda : datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda : datetime.now(timezone.utc))

    model_config = ConfigDict(
        name = "oauth_accounts"
    )
    
    @before_event(Update)
    def set_update(self):
        self.updated_at = datetime.now(tz=timezone.utc)