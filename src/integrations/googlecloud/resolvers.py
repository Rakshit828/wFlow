from src.integrations.googlecloud import GoogleAPIClient, CredentialsModel
from src.repositories.app_integrations import AppIntegrationsRepository
from src.schemas.mongo_projections import CredentialsAndDataForApiClient
from src.workflows.nodes import NODES_MAP
from typing import Type
from pydantic import BaseModel
from src.workflows.types import ApplicationNode


class GoogleNodeConfigResolver:
    def __init__(self):
        pass

    async def resolve(self, node_key: str, user_id: str) -> dict:
        node: ApplicationNode = NODES_MAP.get(node_key)
        service: str = node.service

        config_model: Type[BaseModel] = node.node_input_model.model_fields[
            "config"
        ].annotation
        print(f"The config model is : {config_model}")
        if not node:
            raise Exception(f"Node with key {node_key} not found.")

        integration_repo: AppIntegrationsRepository = AppIntegrationsRepository()

        credentials: CredentialsAndDataForApiClient | None = (
            await integration_repo.find_app_integration(
                user_id=user_id,
                provider="google",
                service=service.split(".")[-1],
                projection_model=CredentialsAndDataForApiClient,
            )
        )
        if not credentials:
            raise Exception("No credentials found")
        credentials = credentials[0]

        print("Credentials are : ", credentials)

        api_client = GoogleAPIClient(
            integration_repo=integration_repo,
            service=credentials.service,
            req_timeout=30.0,
            base_url="https://www.googleapis.com",
            credentials=CredentialsModel(
                user_id=credentials.user_id,
                integration_id=credentials.integration_id,
                service=credentials.service,
                access_token=credentials.access_token,
                refresh_token=credentials.refresh_token,
                scopes=credentials.scopes,
                access_token_expiry=credentials.access_token_expiry,
                refresh_token_expiry=credentials.refresh_token_expiry,
            ),
        )

        model = config_model.set_client(api_client).model_dump()

        print(f"This is the model : {model}")

        return model
