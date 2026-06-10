from pydantic import BaseModel, ConfigDict, computed_field, Field, model_validator
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Literal, TypedDict
from datetime import datetime
from enum import Enum

from src.core.security import decrypt_payload


class MetadataFiltersOptions(TypedDict):
    criteria: Literal["eq", "lt", "lte", "gt", "gte", "neq"]
    value: str | int | float


class CredentialsTypeEnum(str, Enum):
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"


class OAuth2CredentialsPayload(BaseModel):
    access_token: str
    access_token_expiry: datetime
    refresh_token: Optional[str] = None
    refresh_token_expiry: Optional[datetime] = None


class ApiKeyPayload(BaseModel):
    api_key: str


class CredentialsAndDataForApiClient(BaseModel):
    id: str = Field(alias="_id")
    service: str
    user_id: str
    access_token_enc: str
    refresh_token_enc: str | None = None
    access_token_expiry: datetime | None = None
    refresh_token_expiry: datetime | None = None
    scopes: list[str]
    metadata: dict | None = None

    @computed_field
    @property
    def integration_id(self) -> str:
        return str(self.id)

    @computed_field
    @property
    def access_token(self) -> str:
        return decrypt_payload(self.access_token_enc)

    @computed_field
    @property
    def refresh_token(self) -> str:
        return decrypt_payload(self.refresh_token_enc)

    model_config = ConfigDict(extra="ignore")
