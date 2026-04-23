from fastapi import APIRouter, Request, Depends, Response, Query, Path
from fastapi.responses import RedirectResponse
from loguru import logger
from datetime import datetime, timedelta, timezone

from src.db.redis import Redis, get_redis
from src.integrations.googlecould.oauth2 import GoogleOAuthInterface
from src.integrations.googlecould.types import (
    GoogleNewScopeResponse,
)
from src.dependencies.auth import AccessTokenBearer
from src.db.mongo.schemas import Users, AppIntegrations
from src.repositories.auth_repository import UserRepository
from src.repositories.app_integrations import AppIntegrationsRepository
from src.utils.exceptions import AuthErrors, AppError
from src.integrations.exceptions import GeneralIntegrationErrors
from src.integrations.googlecould.scopes import GOOGLE_SERVICES, GOOGLE_SCOPES



integration_router = APIRouter()
google_oauth = GoogleOAuthInterface()


@integration_router.get("/google/new-scope")
async def google_new_scope_redirect(
    scopes: list[str] = Query(...),
    redis: Redis = Depends(get_redis),
    decoded_token: str = Depends(AccessTokenBearer()),
    integration_repo: AppIntegrationsRepository = Depends(AppIntegrationsRepository),
):
    user_id: str = decoded_token["sub"]
    logger.info(f"User id is : {user_id}")
    if scopes:
        service_requested = set()
        for scope in scopes:
            service_requested.add(scope.split(".")[0])
        service: set[str] = service_requested.intersection(GOOGLE_SERVICES)
        if len(service) > 1:
            raise AppError(
                data=None,
                detail=GeneralIntegrationErrors.REQUESTED_MULTIPLE_SERVICE_SCOPE_ERROR.value,
            )
        service = list(service)[0].lower()
        logger.info(f"Service requested is : {service}")
        if service not in GOOGLE_SERVICES:
            raise AppError(
                data=None,
                detail=GeneralIntegrationErrors.INVALID_SERVICE_REQUESTED_ERROR.value,
            )

    integration: AppIntegrations | None = await integration_repo.find_app_integration(
        user_id=user_id, provider="google", service=service
    )
    if integration is not None:
        existing_scopes: list[str] = integration.scopes
        for scope in scopes:
            if GOOGLE_SCOPES[scope] not in existing_scopes:
                existing_scopes.append(GOOGLE_SCOPES[scope])

        scopes = existing_scopes

    url: str = await google_oauth.create_authorization_url(
        db=redis,
        scopes_requested=scopes,
        login_redirect=False,
    )
    logger.debug(f"The url constructed is : {url}")
    return RedirectResponse(url)


@integration_router.get("/google/scope/callback")
async def grant_new_scope(
    code: str,
    state: str,
    decoded_token: str = Depends(AccessTokenBearer()),
    redis: Redis = Depends(get_redis),
    user_repo: UserRepository = Depends(UserRepository),
    integration_repo: AppIntegrationsRepository = Depends(AppIntegrationsRepository),
):
    user_id: str = decoded_token["sub"]
    user: Users | None = await user_repo.get_user_by_id(user_id=user_id)
    logger.info(f"User id decoded is: {user_id}")
    if not user:
        raise AppError(detail=AuthErrors.USER_NOT_FOUND_ERROR.value, data=None)

    tokens: dict[str, str] = await google_oauth.exchange_for_code_new_authorization(
        db=redis, code=code, state=state
    )
    new_scope_response: GoogleNewScopeResponse = (
        await google_oauth.get_openid_payload_new_authorization(tokens)
    )

    if not user:
        raise AppError(AuthErrors.USER_NOT_FOUND_WHEN_UPDATING_SCOPE.value, data=None)

    now = datetime.now(timezone.utc)
    is_updated: bool = await integration_repo.update_existing_integration(
        user_id=user.id,
        provider="google",
        service=new_scope_response.service,
        scopes=new_scope_response.scopes,
        access_token=new_scope_response.access_token,
        refresh_token=new_scope_response.refresh_token,
        access_token_expiry=now + timedelta(seconds=new_scope_response.expires_in),
        
    )
    logger.info(f"Update : {is_updated}")
    if not is_updated:
        await integration_repo.add_new_integration(
            user_ref=user,
            provider="google",
            service=new_scope_response.service,
            scopes=new_scope_response.scopes,
            access_token=new_scope_response.access_token,
            refresh_token=new_scope_response.refresh_token,
            access_token_expiry=now + timedelta(seconds=new_scope_response.expires_in),
            refresh_token_expiry=now + timedelta(seconds=new_scope_response.refresh_expires_in),
            metadata={
                "email": new_scope_response.decoded_id_token.email,
                "is_verified": new_scope_response.decoded_id_token.email_verified,
                "sub": new_scope_response.decoded_id_token.sub,
            },
        )

    return {"message": "Service integrated successfully."}
