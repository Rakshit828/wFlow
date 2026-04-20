from fastapi import APIRouter, Request, Depends, Response, HTTPException, status
from fastapi.responses import RedirectResponse
from loguru import logger
import jwt

from src.db.redis import Redis, get_redis
from src.integrations.googlecould.oauth2 import GoogleOAuthInterface
from src.integrations.constants import GOOGLE_OPENID_SCOPES
from src.db.postgres.setup import get_session, AsyncSession
from src.integrations.googlecould.types import GoogleAuthResponse, GoogleNewScopeResponse
from src.repositories.auth_repository import (
    UserRepository,
    AppIntegrationsCredentialsRepository,
    OAuthAccountsRepository,
)
from src.models.auth_models import LoginResponse
from src.services.tokens import (
    create_jwt_token,
    set_cookies
)
from src.utils.exceptions import AuthErrors, AppError

auth_router = APIRouter()

google_oauth = GoogleOAuthInterface()


@auth_router.get("/google/login")
async def google_login_redirect(redis: Redis = Depends(get_redis)):
    url: str = await google_oauth.create_authorization_url(
        db=redis, scopes_requested=GOOGLE_OPENID_SCOPES
    )
    logger.debug(f"The url constructed is : {url}")
    return RedirectResponse(url)



@auth_router.get("/google/callback", response_model=LoginResponse)
async def google_callback_and_exchange_codes(
    code: str,
    state: str,
    response: Response,
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
    user_repo: UserRepository = Depends(UserRepository),
    integration_repo: AppIntegrationsCredentialsRepository = Depends(
        AppIntegrationsCredentialsRepository
    ),
    oauth_repo: OAuthAccountsRepository = Depends(OAuthAccountsRepository),
) -> LoginResponse:
    """Callback for google login."""
    tokens: dict[str, str] = await google_oauth.exchange_for_code(
        db=redis, code=code, state=state
    )
    auth_response: GoogleAuthResponse = await google_oauth.get_openid_auth_payload(tokens)

    user = await user_repo.get_user_by_email(
        session, auth_response.decoded_id_token.email
    )

    if not user:
        # Create rows only if the user doesn't exist.
        user = await user_repo.create_user(
            session=session,
            email=auth_response.decoded_id_token.email,
            name=auth_response.decoded_id_token.name,
            avatar_url=str(auth_response.decoded_id_token.picture),
            is_verified=auth_response.decoded_id_token.email_verified,
        )

        integration = await integration_repo.create_integration(
            session=session,
            user_id=user.id,
            provider="google",
            access_token=auth_response.access_token,
            refresh_token=auth_response.refresh_token,
            scopes=auth_response.scopes.split(" "),
            access_token_expires_in=auth_response.expires_in,
            token_type=auth_response.token_type,
        )

        await oauth_repo.create_oauth_account(
            session=session,
            user_id=user.id,
            integration_id=integration.id,
            provider="google",
            auth_response=auth_response,
        )

    access_token = create_jwt_token(user_id=user.id, token_type="access")
    refresh_token = create_jwt_token(user.id, token_type="refresh")

    set_cookies(response=response, tokens={"access_token": access_token, "refresh_token": refresh_token})

    return LoginResponse(
        user_id=user.id,
        email=user.email,
        created_at=user.created_at,
    )



@auth_router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session)
):
    pass


@auth_router.get("/google/scope/callback")
async def grant_new_scope(
    code: str,
    state: str,
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
    user_repo: UserRepository = Depends(UserRepository),
    integration_repo: AppIntegrationsCredentialsRepository = Depends(
        AppIntegrationsCredentialsRepository
    ),
    oauth_repo: OAuthAccountsRepository = Depends(OAuthAccountsRepository),
):
    tokens: dict[str, str] = await google_oauth.exchange_for_code(
        db=redis, code=code, state=state
    )
    new_scope_response: GoogleNewScopeResponse = await google_oauth.get_openid_auth_payload(tokens)

    user = await user_repo.get_user_by_email(
        session, new_scope_response.decoded_id_token.email
    )

    if not user:
        raise AppError(AuthErrors.USER_NOT_FOUND_WHEN_UPDATING_SCOPE.value, data=None)
    
    await integration_repo.update_with_new_scopes_and_tokens_google(
        session=session,
        user_id=user.id,
        scopes=new_scope_response.scopes,
        access_token=new_scope_response.access_token,
        refresh_token=new_scope_response.refresh_token,
        access_token_expires_in=new_scope_response.expires_in
    )
    return None

