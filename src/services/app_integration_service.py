from loguru import logger
from datetime import datetime, timedelta, timezone

from src.db.models import AppIntegrations, Users
from src.integrations.googlecloud.scopes import GOOGLE_SERVICES, GOOGLE_SCOPES
from src.core.exceptions import GeneralIntegrationErrors, AppError, AuthErrors
from src.repositories.app_integrations import AppIntegrationsRepository
from src.repositories.auth_repository import UserRepository
from src.integrations.googlecloud import GoogleOAuthInterface, GoogleNewScopeResponse
from src.integrations.github.oauth2 import GitHubOAuthInterface
from src.db.redis import Redis
from src.integrations.googlecloud.scopes import (
    GOOGLE_EMAIL_ONLY_OPENID_SCOPE,
    get_scopes,
)


class AppIntegrationService:
    def __init__(self):
        self.integration_repo = AppIntegrationsRepository()
        self.user_repo = UserRepository()
        self.google_oauth = GoogleOAuthInterface()
        self.github_oauth = GitHubOAuthInterface()

    async def create_authz_url_for_new_scope_google(
        self, user_id: str, email: str, scopes: list[str], redis: Redis
    ) -> str:
        logger.info(
            f"Scope is being requested for account: {email} of user id: {user_id}"
        )

        if scopes:
            service_requested = set()
            for scope in scopes:
                service_requested.add(scope.split(".")[0])
            service: set[str] = service_requested.intersection(GOOGLE_SERVICES)
            if not service:
                raise AppError(
                    data=None,
                    detail=GeneralIntegrationErrors.INVALID_SERVICE_REQUESTED_ERROR.value,
                )
            if len(service) > 1:
                raise AppError(
                    data=None,
                    detail=GeneralIntegrationErrors.REQUESTED_MULTIPLE_SERVICE_SCOPE_ERROR.value,
                )

            # This means one service is surely requested.
            service = list(service)[0].lower()
            logger.info(f"Service requested is : {service}")

        integrations: list[AppIntegrations] | None = (
            await self.integration_repo.find_app_integration(
                user_id=user_id, provider="google", service=service
            )
        )
        # Google integration will have email in metadata.
        required_integration = [
            integration
            for integration in integrations
            if integration.metadata["email"] == email
        ]

        if len(required_integration) > 1:
            raise AppError(
                data=None
            )  # This is impossible event considering data is not redundant.


        if required_integration:
            logger.info(f"Required integration is : {required_integration}")
            existing_scopes: list[str] = required_integration[0].scopes
            for scope in scopes:
                if GOOGLE_SCOPES[scope] not in existing_scopes:
                    existing_scopes.append(GOOGLE_SCOPES[scope])

            scopes = existing_scopes
            
        else:
            logger.info(f"Same user is requesting the same service with different email.")
            new_scopes: list[str] = GOOGLE_EMAIL_ONLY_OPENID_SCOPE.split(" ")
            for scope in scopes:
                new_scopes.append(GOOGLE_SCOPES[scope])
            
            scopes = new_scopes



        url: str = await self.google_oauth.create_authorization_url(
            db=redis, scopes_requested=scopes, login_redirect=False
        )
        logger.debug(f"The url constructed is : {url}")
        return url

    async def grant_new_scope_callback_google(
        self, user_id: str, code: str, state: str, redis: Redis
    ):
        user: Users | None = await self.user_repo.get_user_by_id(user_id=user_id)

        if not user:
            raise AppError(
                AuthErrors.USER_NOT_FOUND_WHEN_UPDATING_SCOPE.value, data=None
            )

        tokens: dict[str, str] = (
            await self.google_oauth.exchange_for_code_new_authorization(
                db=redis, code=code, state=state
            )
        )
        new_scope_response: GoogleNewScopeResponse = (
            await self.google_oauth.get_openid_payload_new_authorization(tokens)
        )

        now = datetime.now(timezone.utc)
        is_updated: bool = await self.integration_repo.update_google_app_integration(
            user_id=user.id,
            provider="google",
            service=new_scope_response.service,
            email=new_scope_response.decoded_id_token.email,
            scopes=new_scope_response.scopes,
            access_token=new_scope_response.access_token,
            refresh_token=new_scope_response.refresh_token,
            access_token_expiry=now + timedelta(seconds=new_scope_response.expires_in),
            refresh_token_expiry=now
            + timedelta(seconds=new_scope_response.refresh_token_expires_in),
        )
        logger.info(f"Update status is: {is_updated}")
        if not is_updated:
            logger.info("Creating new integration. ")
            await self.integration_repo.add_new_integration(
                user_ref=user,
                provider="google",
                service=new_scope_response.service,
                scopes=new_scope_response.scopes,
                access_token=new_scope_response.access_token,
                refresh_token=new_scope_response.refresh_token,
                access_token_expiry=now
                + timedelta(seconds=new_scope_response.expires_in),
                refresh_token_expiry=now
                + timedelta(seconds=new_scope_response.refresh_token_expires_in),
                metadata={
                    "email": new_scope_response.decoded_id_token.email,
                    "is_verified": new_scope_response.decoded_id_token.email_verified,
                    "sub": new_scope_response.decoded_id_token.sub,
                },
            )

        return {"message": "Service integrated successfully."}
