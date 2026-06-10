from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from loguru import logger
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.db.redis import Redis, get_redis
from src.db.postgres.schemas import Users
from src.integrations.services.Google.oauth2 import GoogleOAuthInterface
from src.domains.users.schemas import UserSessionResponse
from src.domains.users.dependency import get_user_service
from src.domains._shared.dependencies import get_session
from src.domains.users.serivce import UserService
from src.core.response import SuccessResponse
from src.config import CONFIG
from src.domains._shared.dependencies import get_user_and_session, UserAndSessionData

auth_router = APIRouter()

google_oauth = GoogleOAuthInterface()


@auth_router.get("/me", response_model=SuccessResponse[UserSessionResponse])
async def get_current_session(
    current_user: UserAndSessionData = Depends(get_user_and_session),
) -> SuccessResponse[UserSessionResponse]:
    """Return the authenticated user from the access_token cookie."""
    user: Users = current_user.get_user()

    user_data = UserSessionResponse(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
    )
    return SuccessResponse[UserSessionResponse](data=user_data)


@auth_router.get("/google/login")
async def google_login_redirect(
    redis: Redis = Depends(get_redis),
    user_service: UserService = Depends(get_user_service),
):
    url: str = await user_service.google_login_url(redis=redis, login_redirect=True)
    logger.info(f"Redirecting to {url} ")
    return RedirectResponse(url)


@auth_router.get("/google/callback")
async def google_callback_and_exchange_codes(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
    user_service: UserService = Depends(get_user_service),
):
    """OAuth callback: set session cookies and redirect to the frontend app."""
    redirect = RedirectResponse(url=CONFIG.FRONTEND_URL)

    await user_service.google_login_callback(
        session=session, code=code, state=state, response=redirect, redis=redis
    )
    return redirect
