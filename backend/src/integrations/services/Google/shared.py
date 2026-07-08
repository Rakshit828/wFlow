from pydantic import BaseModel, ConfigDict, Field
from src.integrations.services.Google.service_client import GoogleAPIClient
from src.integrations.services.Google.g_types import CredentialsModel
from src.db.repository.users_integrations_repository import UsersIntegrationsRepository


class CommonBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, extra="ignore", arbitrary_types_allowed=True
    )


class CommonGoogleConfigModel(CommonBaseModel):
    credentials: CredentialsModel = Field(json_schema_extra={"x-autofilled": True})
    service: str = Field(json_schema_extra={"x-autofilled": True})

    def get_google_api_client(self) -> GoogleAPIClient:
        return GoogleAPIClient(
            credentials=self.credentials,
            integration_repo=UsersIntegrationsRepository(),
            service=self.service,
            req_timeout=30.0,
            base_url="https://www.googleapis.com",
        )
