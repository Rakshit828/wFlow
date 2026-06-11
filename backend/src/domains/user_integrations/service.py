import json
from loguru import logger
from datetime import datetime, timezone, timedelta
from typing import Literal
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.db.repository.users_integrations_repository import UsersIntegrationsRepository
from src.domains.users.repository import UserRepository

from src.integrations.services.Google import (
    GoogleOAuthInterface,
    GoogleNewScopeResponse,
)
from src.integrations.services.Google.scopes import (
    INITIAL_SCOPES_FOR_SERVICE,
    GOOGLE_EMAIL_ONLY_OPENID_SCOPE,
    GOOGLE_SCOPES,
)
from src.core.security import encrypt_payload
from src.db.redis import Redis
from src.db.postgres.schemas import (
    UsersIntegrations,
    CredentialsTypeEnum,
)


class GoogleIntegrationService:
    def __init__(self):
        self.integration_repo = UsersIntegrationsRepository()
        self.user_repo = UserRepository()
        self.google_oauth = GoogleOAuthInterface()

    @property
    def credentials_type(self):
        return CredentialsTypeEnum.OAUTH2

    async def create_authz_url_for_service_scopes_google(
        self, user_id: str, service: Literal["gmail", "drive", "sheets"], redis: Redis
    ) -> str:
        logger.info(f"Scope is being requested for {service} by user: {user_id}")
        scopes = GOOGLE_EMAIL_ONLY_OPENID_SCOPE + [
            GOOGLE_SCOPES[scope] for scope in INITIAL_SCOPES_FOR_SERVICE[service]
        ]

        url: str = await self.google_oauth.create_authorization_url(
            db=redis, scopes_requested=scopes, login_redirect=False
        )
        logger.debug(f"The url constructed is : {url}")
        return url

    async def grant_new_scope_callback_google(
        self, session: AsyncSession, user_id: str, code: str, state: str, redis: Redis
    ) -> UsersIntegrations:
        tokens: dict[str, str] = (
            await self.google_oauth.exchange_for_code_new_authorization(
                db=redis, code=code, state=state
            )
        )
        new_scope_response: GoogleNewScopeResponse = (
            await self.google_oauth.get_openid_payload_new_authorization(tokens)
        )
        now = datetime.now(timezone.utc)
        access_token_expiry = now + timedelta(seconds=new_scope_response.expires_in)
        refresh_token_expiry = now + timedelta(
            seconds=new_scope_response.refresh_token_expires_in
        )
        credentials_payload = {
            "access_token": new_scope_response.access_token,
            "refresh_token": new_scope_response.refresh_token,
            "access_token_expiry": access_token_expiry.isoformat(),
            "refresh_token_expiry": refresh_token_expiry.isoformat(),
        }

        service = "google" + "." + new_scope_response.service

        encrypted_payload = encrypt_payload(json.dumps(credentials_payload))
        logger.info(f"new_scope_response: {new_scope_response}")
        updated = await self.integration_repo.update_integration(
            session=session,
            user_id=user_id,
            service=service,
            update_values={
                "credentials": encrypted_payload,
                "scopes": new_scope_response.scopes,
            },
            metadata_filters={
                "email": {
                    "criteria": "eq",
                    "value": new_scope_response.decoded_id_token.email,
                }
            },
        )
        if updated:
            logger.info(f"Updated integration is : {updated}")
            return updated

        logger.info(f"Did not found integration, creating new one:")
        integration = UsersIntegrations(
            user_id=user_id,
            service=service,
            credentials_type=self.credentials_type,
            credentials=encrypted_payload,
            scopes=new_scope_response.scopes,
            meta={"email": new_scope_response.decoded_id_token.email},
        )
        new_integration = await self.integration_repo.create_new_integration(
            session=session, integration=integration
        )
        logger.info(f"Integration created: {new_integration}")

        return new_integration
