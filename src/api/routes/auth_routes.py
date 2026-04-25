from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from loguru import logger

from src.db.redis import Redis, get_redis
from src.integrations.googlecloud.oauth2 import GoogleOAuthInterface
from src.schemas.auth_schemas import LoginResponse
from src.api.dependencies import get_user_service
from src.services.user_service import UserService




auth_router = APIRouter()

google_oauth = GoogleOAuthInterface()


@auth_router.get("/google/login")
async def google_login_redirect(redis: Redis = Depends(get_redis)):
    url: str = await google_oauth.create_authorization_url(
        db=redis, login_redirect=True
    )
    logger.info(f"Redirecting to {url} ")
    return RedirectResponse(url)


@auth_router.get("/google/callback", response_model=LoginResponse)
async def google_callback_and_exchange_codes(
    code: str,
    state: str,
    response: Response,
    redis: Redis = Depends(get_redis),
    user_service: UserService = Depends(get_user_service),
) -> LoginResponse:
    """Callback for google login."""
    response: LoginResponse = await user_service.google_login_callback(
        code=code, state=state, response=response, redis=redis
    )
    return response