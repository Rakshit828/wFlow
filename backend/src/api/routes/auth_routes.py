import os

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from loguru import logger

from src.db.redis import Redis, get_redis
from src.db.models import Users
from src.integrations.googlecloud.oauth2 import GoogleOAuthInterface
from src.schemas.auth_schemas import UserSessionResponse
from src.api.dependencies import get_user_service, get_current_user
from src.services.user_service import UserService

auth_router = APIRouter()

google_oauth = GoogleOAuthInterface()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@auth_router.get("/me", response_model=UserSessionResponse)
async def get_current_session(
    user: Users = Depends(get_current_user),
) -> UserSessionResponse:
    """Return the authenticated user from the access_token cookie."""
    return UserSessionResponse(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
    )


@auth_router.get("/google/login")
async def google_login_redirect(redis: Redis = Depends(get_redis)):
    url: str = await google_oauth.create_authorization_url(
        db=redis, login_redirect=True
    )
    logger.info(f"Redirecting to {url} ")
    return RedirectResponse(url)


@auth_router.get("/google/callback")
async def google_callback_and_exchange_codes(
    code: str,
    state: str,
    redis: Redis = Depends(get_redis),
    user_service: UserService = Depends(get_user_service),
):
    """OAuth callback: set session cookies and redirect to the frontend app."""
    redirect = RedirectResponse(url=FRONTEND_URL)
    await user_service.google_login_callback(
        code=code, state=state, response=redirect, redis=redis
    )
    return redirect
