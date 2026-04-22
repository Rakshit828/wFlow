from src.db.mongo.schemas import AppIntegrations, Users
from src.repositories.auth_repository import UserRepository
from src.services.encryption import encrypt_token
from datetime import datetime
from loguru import logger


class AppIntegrationsRepository:
    def __init__(self):
        self.__user_repo: UserRepository = UserRepository()

    async def add_new_integration(
        self,
        user_ref: str | Users,
        access_token: str,
        access_token_expiry: datetime,
        provider: str,
        service: str,
        refresh_token: str | None,
        refresh_token_expiry: datetime | None = None,
        scopes: list[str] | None = None,
        metadata: dict | None = None,
    ):
        if not isinstance(user_ref, Users):
            user: Users | None = self.__user_repo.get_user_by_id(user_id=user_ref)
        else:
            user = user_ref
            
        if not user:
            logger.error(f"User with id {user_ref} doesn't exist.")
            return None

        if scopes is None:
            scopes = []

        encrypted_access_token = encrypt_token(access_token)
        encrypted_refresh_token = (
            encrypt_token(refresh_token) if refresh_token else None
        )

        integration: AppIntegrations | None = await AppIntegrations.insert_one(
            AppIntegrations(
                user=user,
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
