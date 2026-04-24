from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from src.db.redis import Redis, get_redis
from src.api.dependencies import (
    AccessTokenBearer,
    get_app_integration_service,
    get_user_service,
)
from src.services.app_integration_service import AppIntegrationService


integration_router = APIRouter()


@integration_router.get("/google/new-scope")
async def google_new_scope_redirect(
    scopes: list[str] = Query(...),
    redis: Redis = Depends(get_redis),
    integration_service: AppIntegrationService = Depends(get_app_integration_service),
    decoded_token: str = Depends(AccessTokenBearer),
):
    user_id: str = decoded_token["sub"]
    url = await integration_service.create_authz_url_for_new_scope_google(
        user_id=user_id, scopes=scopes, redis=redis
    )
    return RedirectResponse(url)


@integration_router.get("/google/scope/callback")
async def grant_new_scope(
    code: str,
    state: str,
    decoded_token: str = Depends(AccessTokenBearer()),
    redis: Redis = Depends(get_redis),
    integration_repo: AppIntegrationService = Depends(get_app_integration_service),
):
    user_id: str = decoded_token["sub"]
    response = await integration_repo.grant_new_scope_callback_google(
        user_id=user_id, code=code, state=state, redis=redis
    )
    return response
