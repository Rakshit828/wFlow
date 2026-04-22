from fastapi import APIRouter, Request, Depends, Response
from fastapi.responses import RedirectResponse
from loguru import logger
from datetime import datetime, timedelta, timezone

from src.db.redis import Redis, get_redis
from src.integrations.googlecould.oauth2 import GoogleOAuthInterface
from src.integrations.constants import GOOGLE_OPENID_SCOPES, GOOGLE_EMAIL_READONLY_SCOPE
from src.integrations.googlecould.types import (
    GoogleAuthResponse,
    GoogleNewScopeResponse,
)
from src.models.auth_models import LoginResponse
from src.services.tokens import create_jwt_tokens, set_cookies
from src.dependencies.auth import AccessTokenBearer
from src.db.mongo.schemas import Users, OAuthAccounts, AppIntegrations
from src.repositories.auth_repository import UserRepository, OAuthAccountRepository
from src.repositories.app_integrations import AppIntegrationsRepository
from src.utils.exceptions import AuthErrors, AppError
from typing import Literal

auth_router = APIRouter()

google_oauth = GoogleOAuthInterface()


@auth_router.get("/google/redirect-url/{purpose}")
async def google_login_redirect(
    purpose: Literal["login", "new_scope"],
    scope: str | None = None,
    redis: Redis = Depends(get_redis),
):
    login_redirect = False
    match (purpose):
        case "login":
            login_redirect = True
            scopes = GOOGLE_OPENID_SCOPES if scope is None else scope
        case "new_scope":
            if scope == "gmail.readonly":
                scopes = GOOGLE_EMAIL_READONLY_SCOPE
        case _:
            pass

    url: str = await google_oauth.create_authorization_url(
        db=redis, scopes_requested=scopes, login_redirect=login_redirect
    )
    logger.debug(f"The url constructed is : {url}")
    return RedirectResponse(url)


@auth_router.get("/google/callback", response_model=LoginResponse)
async def google_callback_and_exchange_codes(
    code: str,
    state: str,
    response: Response,
    redis: Redis = Depends(get_redis),
    user_repo: UserRepository = Depends(UserRepository),
    oauth_repo: OAuthAccountRepository = Depends(OAuthAccountRepository),
) -> LoginResponse:
    """Callback for google login."""
    tokens: dict[str, str] = await google_oauth.exchange_for_code(
        db=redis, code=code, state=state
    )
    auth_response: GoogleAuthResponse = await google_oauth.get_openid_auth_payload(
        tokens
    )

    user = await user_repo.get_user_by_email(auth_response.decoded_id_token.email)

    if not user:
        # Create rows only if the user doesn't exist.
        user: Users | None = await user_repo.create_user(
            email=auth_response.decoded_id_token.email,
            name=auth_response.decoded_id_token.name,
            username=None,
            avatar_url=str(auth_response.decoded_id_token.picture),
            is_verified=auth_response.decoded_id_token.email_verified,
        )

        if user is None:
            raise AppError()

        await oauth_repo.create_oauth_account(
            user_ref=user.id,
            provider="google",
            provider_email=auth_response.decoded_id_token.email,
            is_email_verified=auth_response.decoded_id_token.email_verified,
            scopes=auth_response.scopes,
            provider_sub_id=auth_response.decoded_id_token.sub,
            access_token=auth_response.access_token,
            refresh_token=auth_response.refresh_token,
            access_token_expiry=auth_response.expires_in,
            refresh_token_expiry=None,
        )

    tokens = await create_jwt_tokens(user.id, is_login=True)

    set_cookies(
        response=response,
        tokens={
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        },
    )

    return LoginResponse(
        user_id=user.id,
        email=user.email,
        created_at=user.created_at,
    )


@auth_router.get("/google/scope/callback")
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
    await integration_repo.add_new_integration(
        user_ref=user,
        provider="google",
        service="google",  # Later add this logic of selecting service.
        scopes=new_scope_response.scopes,
        access_token=new_scope_response.access_token,
        refresh_token=new_scope_response.refresh_token,
        access_token_expiry=now + timedelta(seconds=new_scope_response.expires_in),
        refresh_token_expiry=None,
    )

    return {"message": "Service integrated successfully."}
