from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from loguru import logger

from src.db.redis import Redis, get_redis
from src.integrations.googlecould.oauth2 import GoogleOAuthInterface
from src.integrations.constants import GOOGLE_OPENID_SCOPES
from src.db.postgres.setup import get_session, AsyncSession
from src.integrations.googlecould.types import GoogleAuthResponse
from src.repositories.auth_repository import (
    UserRepository,
    AppIntegrationsCredentialsRepository,
    OAuthAccountsRepository,
)
from src.models.auth_models import LoginResponse

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
    redis: Redis = Depends(get_redis),
    session: AsyncSession = Depends(get_session),
    user_repo: UserRepository = Depends(UserRepository),
    integration_repo: AppIntegrationsCredentialsRepository = Depends(
        AppIntegrationsCredentialsRepository
    ),
    oauth_repo: OAuthAccountsRepository = Depends(OAuthAccountsRepository),
) -> LoginResponse:

    auth_response: GoogleAuthResponse = await google_oauth.exchange_for_code(
        db=redis, code=code, state=state
    )

    user = await user_repo.get_user_by_email(
        session, auth_response.decoded_id_token.email
    )

    if not user:
        # 2. Create User if New
        user = await user_repo.create_user(
            session=session,
            email=auth_response.decoded_id_token.email,
            name=auth_response.decoded_id_token.name,
            avatar_url=str(auth_response.decoded_id_token.picture),
            is_verified=auth_response.decoded_id_token.email_verified,
        )

    # If user already exists update has to be done.
    # Will be handled later.

    integration = await integration_repo.create_integration(
        session=session,
        user_id=user.id,
        provider="google",
        access_token=auth_response.access_token,
        refresh_token=auth_response.refresh_token,
        scopes=auth_response.scope.split(" "),
        expires_in=auth_response.expires_in,
    )

    await oauth_repo.create_oauth_account(
        session=session,
        user_id=user.id,
        integration_id=integration.id,
        provider="google",
        auth_response=auth_response,
    )

    return LoginResponse(user_id=user.id, email=user.email, created_at=user.created_at)
