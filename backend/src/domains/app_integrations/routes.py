from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from typing import Literal
from loguru import logger

from src.db.redis import Redis, get_redis
from src.domains._shared.dependencies import AccessTokenBearer
from src.domains.app_integrations.dependency import get_google_integration_service
from src.domains.app_integrations.service import GoogleIntegrationService

integration_router = APIRouter()

# @integration_router.get("/discord/url")
# async def discord_login_redirect(
#     tier: Literal["basic", "pro"] = Query(...),
#     # decoded_token: str = Depends(AccessTokenBearer()),
# ):
#     # user_id: str = decoded_token["sub"]
#     url = await discord_oauth.create_authorization_url(tier=tier)
#     logger.info(f"The url is : {url}")
#     return RedirectResponse(url)


# @integration_router.get("/discord/scope/callback")
# async def discord_scope_callback(
#     code: str,
#     decoded_token: str = Depends(AccessTokenBearer()),
#     redis: Redis = Depends(get_redis),
# ):
#     response: dict[str, str] = await discord_oauth.exchange_for_code(code=code)
#     print(response)
#     return response


@integration_router.get("/google/new-scope")
async def google_new_scope_redirect(
    scopes: list[str] = Query(...),
    email: str = Query(...),
    redis: Redis = Depends(get_redis),
    integration_service: GoogleIntegrationService = Depends(
        get_google_integration_service
    ),
    decoded_token: str = Depends(AccessTokenBearer()),
):
    user_id: str = decoded_token["sub"]
    url = await integration_service.create_authz_url_for_new_scope_google(
        user_id=user_id, email=email, scopes=scopes, redis=redis
    )
    return RedirectResponse(url)


@integration_router.get("/google/scope/callback")
async def grant_new_scope(
    code: str,
    state: str,
    decoded_token: str = Depends(AccessTokenBearer()),
    redis: Redis = Depends(get_redis),
    integration_repo: GoogleIntegrationService = Depends(
        get_google_integration_service
    ),
):
    user_id: str = decoded_token["sub"]
    response = await integration_repo.grant_new_scope_callback_google(
        user_id=user_id, code=code, state=state, redis=redis
    )
    return response
