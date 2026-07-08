from datetime import datetime, timedelta, timezone
import httpx
from typing import cast, Any
from loguru import logger
from src.integrations.components.service_client import ServiceRequestHandler
from src.integrations.components.api_client import ApiClient
from src.integrations.components.credentials import CredentialsManager
from src.integrations.components.api_client import RequestOptions
from src.integrations.components.exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitingError,
)
from src.integrations.services.Google.g_types import (
    GoogleApiErrorResponse,
    GoogleErrorStatus,
)
from src.integrations.components.credentials import CredentialsModel
from src.config import CONFIG
from .g_types import GoogleApis


class GoogleRequestHandler(ServiceRequestHandler):

    # Refresh proactively if the token expires within this window.
    _EXPIRY_SKEW = timedelta(seconds=60)

    def __init__(
        self, api_client: ApiClient, creds_manager: CredentialsManager
    ) -> None:
        super().__init__(api_client, creds_manager)

    @property
    def service(self) -> str:
        return "GOOGLE"

    async def handle(
        self,
        method: str,
        endpoint: str,
        options: RequestOptions | None = None,
        *,
        _retrying: bool = False,
    ) -> tuple[httpx.Response, dict[str, Any]]:
        """Perform an authenticated request against a Google API (Gmail, Drive, ...).

        Proactively refreshes the token if it's near expiry, and reactively
        refreshes + retries once on a 401. Raises typed exceptions for
        rate limiting, auth failures, and other non-2xx responses.
        """
        user_id: str = self._creds_manager.user_id

        credentials = await self._creds_manager.get_credentials(user_id, self.service)

        if self._is_token_expired(credentials) and not _retrying:
            credentials = await self.refetch_credentials(user_id)

        merged_options: RequestOptions = dict(options or {})  # type: ignore[assignment]
        headers = dict(merged_options.get("headers") or {})
        headers["Authorization"] = f"Bearer {credentials.access_token}"
        merged_options["headers"] = headers

        response, response_json = await self._api_client.request(
            method, endpoint, merged_options
        )
        response_body: GoogleApiErrorResponse = cast(
            GoogleApiErrorResponse, response_json
        )

        if response_body["code"] == 401 and not _retrying:
            logger.warning(
                f"Got 401 from Google API for user={user_id}; refreshing token and retrying once"
            )
            await self.refetch_credentials(user_id)
            return await self.handle(method, endpoint, options, _retrying=True)

        if (
            response_body["code"] == 401
            and response_body["status"] == GoogleErrorStatus.UNAUTHENTICATED
        ):
            logger.error(f"[ERROR]: {response_body}")
            raise AuthenticationError(
                f"Google API request to {endpoint} still unauthorized after token refresh"
            )

        if (
            response_body["code"] == 429
            and response_body["status"] == GoogleErrorStatus.RESOURCE_EXHAUSTED
        ):
            logger.error(f"[ERROR]: {response_body}")
            retry_after = response.headers.get("Retry-After")
            raise RateLimitingError(
                f"Rate limited by Google API on {endpoint}",
                meta={"retry_after": float(retry_after) if retry_after else None},
            )

        if response_body["status"] == GoogleErrorStatus.PERMISSION_DENIED:
            logger.error(f"[ERROR]: {response_body}")
            raise AuthorizationError(
                message=response_body["message"],
                meta={"errors": response_body["errors"]},
            )

        if response.status_code >= 400:
            logger.error(f"Google API error [ERROR]: {response_body}")
            raise

        return response, response_json

    async def refetch_credentials(self, user_id: str) -> CredentialsModel:
        """Refetch the credentials, save in the database using CredentialsManager and return the CredentialsModel."""
        credentials = await self._creds_manager.get_credentials(user_id, self.service)

        refresh_token: str | None = getattr(credentials, "refresh_token", None)

        if not refresh_token:
            raise AuthenticationError(
                message=f"No refresh token stored for user={user_id}; user must re-authorize Google access"
            )

        body = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CONFIG.GOOGLE_CLIENT_ID,
            "client_secret": CONFIG.GOOGLE_CLIENT_SECRET,
        }

        response, response_json = await self._api_client.request(
            "POST",
            GoogleApis.GOOGLE_TOKEN_URL,
            {
                "data": body,
                "json": None,
                "params": None,
                "headers": {"Content-Type": "application/x-www-form-urlencoded"},
                "timeout": 15,
            },
            is_refresh=True,
        )
        response_body: GoogleApiErrorResponse = cast(
            GoogleApiErrorResponse, response_json
        )

        if response_body["code"] != 200:

            if response_body["status"] == GoogleErrorStatus.UNAUTHENTICATED:
                raise AuthenticationError(
                    f"Google refresh token for user={user_id} was revoked or expired; "
                    "user must re-authorize"
                )

            raise Exception(
                f"Google token refresh failed for user={user_id}: {response_body}"
            )

        token_data = response.json()
        new_access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)

        if not new_access_token:
            raise Exception(
                f"Google token refresh response for user={user_id} missing access_token"
            )

        updated_data = credentials.model_dump()
        updated_data["access_token"] = new_access_token
        # Google does not always return a new refresh_token; keep the old one if absent.
        if token_data.get("refresh_token"):
            updated_data["refresh_token"] = token_data["refresh_token"]
        updated_data["expiry"] = (
            datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        ).isoformat()

        new_credentials = self._creds_manager.credentials_model.model_validate(
            updated_data
        )
        await self._creds_manager.update_credentials(
            user_id, self.service, new_credentials
        )
        return new_credentials

    @staticmethod
    def _is_token_expired(credentials: CredentialsModel) -> bool:
        expiry = getattr(credentials, "expiry", None)
        if not expiry:
            return False
        if isinstance(expiry, str):
            try:
                expiry = datetime.fromisoformat(expiry)
            except ValueError:
                return False
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) + GoogleRequestHandler._EXPIRY_SKEW >= expiry
