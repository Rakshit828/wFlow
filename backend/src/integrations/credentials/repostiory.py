from beanie.odm.operators.update.general import Set
from beanie.odm.operators.update.array import AddToSet
from beanie import PydanticObjectId
from bson import ObjectId
from datetime import datetime
from loguru import logger
from typing import TypeVar, Optional, Union, Type, Any, Dict
from pydantic import BaseModel

from src.domains.app_integrations.models import (
    AppIntegrations,
    CredentialsTypeEnum,
    ApiKeyPayload,
    OAuth2CredentialsPayload,
)

ProjectionModelT = TypeVar("ProjectionModelT", bound=BaseModel)



class CredentialsManagementRepository:

    async def find_app_integration_by_id(
        self,
        integration_id: str,
        projection_model: Optional[Type[ProjectionModelT]] = None,
    ) -> Optional[Union[AppIntegrations, ProjectionModelT]]:
        integration = await AppIntegrations.find_one(
            AppIntegrations.id == PydanticObjectId(integration_id),
            projection_model=projection_model if projection_model else AppIntegrations,
        )
        logger.info(f"Integration founded is : {integration}")
        return integration

    async def find_app_integration(
        self,
        user_id: str,
        provider: str,
        service: str,
        meta_filters: Dict[str, str] | None = None,
        projection_model: Optional[Type[ProjectionModelT]] = None,
    ) -> Optional[Union[list[AppIntegrations], list[ProjectionModelT]]]:
        kwargs: dict[str, Any] = {}

        if projection_model:
            kwargs["projection_model"] = projection_model
        else:
            kwargs["projection_model"] = AppIntegrations

        integration = await AppIntegrations.find(
            AppIntegrations.user_id == PydanticObjectId(user_id),
            AppIntegrations.provider == provider,
            AppIntegrations.service == service,
            **kwargs,
        ).to_list()

        logger.info(
            f"Integrations found are :  {integration}. Count: {len(integration)}"
        )
        return integration if integration else None

    async def update_credentials(
        self,
        integration_id: str,
        enc_credentials_payload: str,
    ):
        update_response = await AppIntegrations.find_one(
            AppIntegrations.id == PydanticObjectId(integration_id)
        ).update(
            Set({AppIntegrations.enc_credentials_payload: enc_credentials_payload})
        )
        return update_response


    async def update_google_app_integration(
        self,
        user_id: str | PydanticObjectId | ObjectId,
        provider: str,
        service: str,
        email: str,
        scopes: list[str],
        enc_credentials_payload: str,
    ):
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)

        update_result = await AppIntegrations.find(
            AppIntegrations.user_id == PydanticObjectId(user_id),
            AppIntegrations.provider == provider,
            AppIntegrations.service == service,
            AppIntegrations.metadata.email == email,
        ).update(
            Set({AppIntegrations.enc_credentials_payload: enc_credentials_payload}),
            AddToSet({AppIntegrations.scopes: {"$each": scopes}}),
        )
        if update_result.matched_count == 0:
            return False
        return True


    async def add_new_integration(
        self,
        user_id: str | PydanticObjectId | ObjectId,
        provider: str,
        service: str,
        credentials_type: CredentialsTypeEnum,
        enc_credentials_payload: str,
        scopes: list[str] | None = None,
        metadata: dict | None = None,
    ):
        if not isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)

        if scopes is None:
            scopes = []

        integration: AppIntegrations | None = await AppIntegrations.insert_one(
            AppIntegrations(
                user_id=user_id,
                provider=provider,
                service=service,
                scopes=scopes,
                credentials_type=credentials_type,
                enc_credentials_payload=enc_credentials_payload,
                metadata=metadata,
            )
        )
        return integration
