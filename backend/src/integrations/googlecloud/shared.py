from pydantic import BaseModel, ConfigDict, Field
from src.integrations.googlecloud.google_api_client import GoogleAPIClient
from src.integrations.googlecloud.g_types import CredentialsModel
from src.repositories.app_integrations import AppIntegrationsRepository


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
            integration_repo=AppIntegrationsRepository(),
            service=self.service,
            req_timeout=30.0,
            base_url="https://www.googleapis.com",
        )
