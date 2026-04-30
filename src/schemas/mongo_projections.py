from pydantic import BaseModel, ConfigDict, computed_field, Field
from src.core.security import decrypt_token
from beanie import PydanticObjectId
from typing import Any
from bson.dbref import DBRef
from datetime import datetime


class CredentialsAndDataForApiClient(BaseModel):
    id: PydanticObjectId = Field(alias="_id")
    service: str
    user: Any  # THis is a DBRef, we don't use it since pydantic don't support it.
    access_token_enc: str
    refresh_token_enc: str | None = None
    access_token_expiry: datetime | None = None
    refresh_token_expiry: datetime | None = None
    scopes: list[str]
    metadata: dict | None = None


    @computed_field
    @property
    def user_id(self) -> str:
        return str(self.user.id)

    @computed_field
    @property
    def integration_id(self) -> str:
        return str(self.id)

    @computed_field
    @property
    def access_token(self) -> str:
        return decrypt_token(self.access_token_enc)

    @computed_field
    @property
    def refresh_token(self) -> str:
        return decrypt_token(self.refresh_token_enc)

    model_config = ConfigDict(extra="ignore")
