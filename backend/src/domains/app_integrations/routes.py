from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio.session import AsyncSession
from typing import Literal

from src.db.redis import Redis, get_redis
from src.domains._shared.dependencies import get_user_and_session, UserAndSessionData
from src.domains.app_integrations.dependency import get_google_integration_service
from src.domains.app_integrations.service import GoogleIntegrationService
from src.core.response import SuccessResponse
from src.db.postgres.schemas import Users

integration_router = APIRouter()


@integration_router.get("/google/new-scope")
async def google_new_service_redirect(
    service: Literal["gmail", "drive", "sheets"] = Query(...),
    redis: Redis = Depends(get_redis),
    integration_service: GoogleIntegrationService = Depends(
        get_google_integration_service
    ),
    current_user: UserAndSessionData = Depends(get_user_and_session),
):
    user: Users = current_user.get_user()
    session: AsyncSession = current_user.get_session()

    url = await integration_service.create_authz_url_for_service_scopes_google(
        service=service, user_id=str(user.id), redis=redis
    )
    return RedirectResponse(url)


@integration_router.get("/google/scope/callback")
async def grant_new_scope(
    code: str,
    state: str,
    current_user: UserAndSessionData = Depends(get_user_and_session),
    redis: Redis = Depends(get_redis),
    integration_repo: GoogleIntegrationService = Depends(
        get_google_integration_service
    ),
):
    user: Users = current_user.get_user()
    users_integration = await integration_repo.grant_new_scope_callback_google(
        user_id=str(user.id), code=code, state=state, redis=redis
    )
    return SuccessResponse[None](message="Service Integrated Successfully.")
