from pydantic import BaseModel, ConfigDict, computed_field, Field, model_validator
from src.core.security import decrypt_token
from beanie import PydanticObjectId
from typing import Any
from datetime import datetime


class CredentialsAndDataForApiClient(BaseModel):
    id: PydanticObjectId = Field(alias="_id")
    service: str
    user_id: str
    access_token_enc: str
    refresh_token_enc: str | None = None
    access_token_expiry: datetime | None = None
    refresh_token_expiry: datetime | None = None
    scopes: list[str]
    metadata: dict | None = None

    @model_validator(mode="before")
    @classmethod
    def convert_user_id_to_str(cls, data: dict):
        if not isinstance(data, dict):
            return data

        if "user_id" in data and data["user_id"] is not None:
            data["user_id"] = str(data["user_id"])

        return data

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
