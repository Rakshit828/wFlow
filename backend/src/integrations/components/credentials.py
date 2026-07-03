import json
from typing import Type
from sqlalchemy.ext.asyncio.session import AsyncSession
from src.types.db_types import CredentialsTypeEnum

from src.db.repository.users_integrations_repository import UsersIntegrationsRepository
from src.utils.utils import wrap_in_session
from src.core.security import decrypt_payload, encrypt_payload
from loguru import logger
from .exceptions import CredentialsNotFoundError
from .types import CredentialsModel


class CredentialsManager:
    def __init__(self, credentials_model: Type[CredentialsModel]) -> None:
        self._integrations_repo = UsersIntegrationsRepository()
        self.credentials_model: Type[CredentialsModel] = credentials_model
        self._credentials: CredentialsModel | None = None

    async def get_credentials(self, user_id: str, service: str) -> CredentialsModel:
        if not self._credentials:
            self._credentials = await wrap_in_session(
                self._load_credentials, user_id=user_id, service=service
            )
        return self._credentials

    async def _load_credentials(
        self, session: AsyncSession, user_id: str, service: str
    ) -> CredentialsModel:
        try:
            data: tuple[CredentialsTypeEnum, str] = (
                await self._integrations_repo.load_encrypted_credentials(
                    session=session,
                    user_id=user_id,
                    service=service,
                    metadata_filters=None,
                )
            )
        except Exception as exc:  # repo/db-layer failure
            logger.error(
                f"Failed loading credentials for user={user_id} service={service}: {exc}"
            )
            raise CredentialsNotFoundError(
                f"No credentials found for user={user_id} service={service}"
            ) from exc

        if not data:
            raise CredentialsNotFoundError(
                f"No credentials found for user={user_id} service={service}"
            )

        _, enc_payload = data
        try:
            decoded_creds = decrypt_payload(enc_payload)
            decoded_creds_dict = json.loads(decoded_creds)
            return self.credentials_model.model_validate(decoded_creds_dict)
        except Exception as exc:
            logger.error(
                f"Failed decoding/validating credentials for user={user_id} service={service}: {exc}"
            )
            raise CredentialsNotFoundError(
                f"Stored credentials for user={user_id} service={service} are corrupt or invalid"
            ) from exc

    async def update_credentials(
        self, user_id: str, service: str, new_credentials: CredentialsModel
    ) -> None:
        """Persist refreshed credentials to the DB and update the in-memory cache."""
        self._credentials = new_credentials
        await wrap_in_session(
            self._save_credentials,
            user_id=user_id,
            service=service,
            credentials=new_credentials,
        )

    async def _save_credentials(
        self,
        session: AsyncSession,
        user_id: str,
        service: str,
        credentials: CredentialsModel,
    ) -> None:
        payload = credentials.model_dump_json()
        encrypted_payload = encrypt_payload(payload)
        try:
            await self._integrations_repo.save_encrypted_credentials(
                session=session,
                user_id=user_id,
                service=service,
                encrypted_payload=encrypted_payload,
            )
        except Exception as exc:
            logger.error(
                f"Failed persisting refreshed credentials for user={user_id} service={service}: {exc}"
            )
            raise

    def invalidate(self) -> None:
        """Drop the cached credentials, forcing a reload from the DB next call."""
        self._credentials = None
