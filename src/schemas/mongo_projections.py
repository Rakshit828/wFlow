from pydantic import BaseModel, ConfigDict, computed_field
from src.core.security import decrypt_token
from beanie import PydanticObjectId
from datetime import datetime

class GetCredentialsOfIntegration(BaseModel):
    access_token_enc: str 
    refresh_token_enc: str | None = None
    access_token_expiry: datetime | None = None
    refresh_token_expiry: datetime | None = None
    scopes: list[str]

    @computed_field
    @property
    def access_token(self) -> str:
        return decrypt_token(self.access_token_enc)
    
    @computed_field
    @property
    def refresh_token(self) -> str:
        return decrypt_token(self.refresh_token_enc)

    model_config = ConfigDict(extra="ignore")
