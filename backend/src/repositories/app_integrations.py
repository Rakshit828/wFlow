from beanie.odm.operators.update.general import Set
from beanie.odm.operators.update.array import AddToSet
from beanie import PydanticObjectId
from bson import ObjectId
from datetime import datetime
from loguru import logger
from typing import TypeVar, Optional, Union, Type
from pydantic import BaseModel

from src.db.models import AppIntegrations, Users
from src.repositories.auth_repository import UserRepository
from src.core.security import encrypt_token
from src.schemas.mongo_projections import CredentialsAndDataForApiClient

ProjectionModelT = TypeVar("ProjectionModelT", bound=BaseModel)


class AppIntegrationsRepository:
    def __init__(self):
        self.__user_repo: UserRepository = UserRepository()

    async def find_app_integration_by_id(
        self,
        integration_id: str,
        projection_model: Optional[Type[ProjectionModelT]] = None,
    ) -> Optional[Union[AppIntegrations, CredentialsAndDataForApiClient]]:
        integration = await AppIntegrations.find_one(
            AppIntegrations.id == PydanticObjectId(integration_id),
            projection_model=projection_model if projection_model else AppIntegrations,
        )
        logger.info(f"Integration founded is : {integration}")
        return integration

    async def update_credentials(
        self,
        integration_id: str,
        access_token: str,
        access_token_expiry: datetime,
        refresh_token_expiry: datetime,
    ):
        update_response = await AppIntegrations.find_one(
            AppIntegrations.id == PydanticObjectId(integration_id)
        ).update(
            Set(
                {
                    AppIntegrations.access_token_enc: encrypt_token(access_token),
                    AppIntegrations.access_token_expiry: access_token_expiry,
                    AppIntegrations.refresh_token_expiry: refresh_token_expiry,
                }
            ),
        )
        return update_response

    async def find_app_integration(
        self,
        user_id: str,
        provider: str,
        service: str,
        projection_model: Optional[Type[ProjectionModelT]] = None,
    ) -> Optional[Union[list[AppIntegrations], list[ProjectionModelT]]]:
        kwargs: dict = {}
        
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
        return integration

    async def update_google_app_integration(
        self,
        user_id: str | PydanticObjectId | ObjectId,
        provider: str,
        service: str,
        email: str,
        scopes: list[str],
        access_token: str,
        refresh_token: str,
        access_token_expiry: datetime,
        refresh_token_expiry: datetime,
    ):
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)

        update_result = await AppIntegrations.find(
            AppIntegrations.user_id == PydanticObjectId(user_id),
            AppIntegrations.provider == provider,
            AppIntegrations.service == service,
            AppIntegrations.metadata.email == email,
        ).update(
            Set(
                {
                    AppIntegrations.access_token_enc: encrypt_token(access_token),
                    AppIntegrations.refresh_token_enc: encrypt_token(refresh_token),
                    AppIntegrations.access_token_expiry: access_token_expiry,
                    AppIntegrations.refresh_token_expiry: refresh_token_expiry,
                }
            ),
            AddToSet({AppIntegrations.scopes: {"$each": scopes}}),
        )
        if update_result.matched_count == 0:
            return False
        return True

    async def update_app_integration(
        self,
        integration: AppIntegrations,
        access_token: str,
        refresh_token: str,
        access_token_expiry: datetime,
        refresh_token_expiry: datetime,
        scopes: list[str],
    ) -> bool:

        if integration is None:
            return False
        update_response = await integration.update(
            Set(
                {
                    AppIntegrations.access_token_enc: encrypt_token(access_token),
                    AppIntegrations.refresh_token_enc: encrypt_token(refresh_token),
                    AppIntegrations.access_token_expiry: access_token_expiry,
                    AppIntegrations.refresh_token_expiry: refresh_token_expiry,
                }
            ),
            AddToSet({AppIntegrations.scopes: {"$each": scopes}}),
        )
        logger.info(f"Updated response is : {update_response}")

        return True

    async def add_new_integration(
        self,
        user_id: str | PydanticObjectId | ObjectId,
        access_token: str,
        access_token_expiry: datetime,
        provider: str,
        service: str,
        refresh_token: str | None,
        refresh_token_expiry: datetime | None = None,
        scopes: list[str] | None = None,
        metadata: dict | None = None,
    ):
        if not isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)

        if scopes is None:
            scopes = []

        encrypted_access_token = encrypt_token(access_token)
        encrypted_refresh_token = (
            encrypt_token(refresh_token) if refresh_token else None
        )

        integration: AppIntegrations | None = await AppIntegrations.insert_one(
            AppIntegrations(
                user_id=user_id,
                provider=provider,
                service=service,
                scopes=scopes,
                access_token_enc=encrypted_access_token,
                access_token_expiry=access_token_expiry,
                refresh_token_enc=encrypted_refresh_token,
                refresh_token_expiry=refresh_token_expiry,
                metadata=metadata,
            )
        )
        return integration
