from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from loguru import logger

from src.db.redis import Redis, get_redis
from src.integrations.googlecould.oauth2 import GoogleOAuthInterface
from src.integrations.googlecould.types import (
    GoogleAuthResponse,
)
from src.models.auth_models import LoginResponse
from src.services.tokens import create_jwt_tokens, set_cookies
from src.db.mongo.schemas import Users
from src.repositories.auth_repository import UserRepository, OAuthAccountRepository
from src.utils.exceptions import AuthErrors, AppError


auth_router = APIRouter()

google_oauth = GoogleOAuthInterface()


@auth_router.get("/google/login")
async def google_login_redirect(redis: Redis = Depends(get_redis)):
    url: str = await google_oauth.create_authorization_url(
        db=redis, login_redirect=True
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