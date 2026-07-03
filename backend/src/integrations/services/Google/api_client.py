from datetime import datetime, timedelta, timezone
import httpx
from loguru import logger
from src.integrations.components.service_client import ServiceRequestHandler
from src.integrations.components.api_client import ApiClient
from src.integrations.components.credentials import CredentialsManager
from src.integrations.components.api_client import RequestOptions
from src.integrations.components.exceptions import CredentialsRevokedError
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

    # ------------------------------------------------------------------ #
    # Generic authenticated request
    # ------------------------------------------------------------------ #

    async def handle(
        self,
        method: str,
        endpoint: str,
        user_id: str,
        options: RequestOptions | None = None,
        *,
        _retrying: bool = False,
    ) -> httpx.Response:
        """Perform an authenticated request against a Google API (Gmail, Drive, ...).

        Proactively refreshes the token if it's near expiry, and reactively
        refreshes + retries once on a 401. Raises typed exceptions for
        rate limiting, auth failures, and other non-2xx responses.
        """

        credentials = await self._creds_manager.get_credentials(user_id, self.service)

        if self._is_token_expired(credentials) and not _retrying:
            credentials = await self.refetch_credentials(user_id)

        merged_options: RequestOptions = dict(options or {})  # type: ignore[assignment]
        headers = dict(merged_options.get("headers") or {})
        headers["Authorization"] = f"Bearer {credentials.access_token}"
        merged_options["headers"] = headers

        response = await self._api_client.request(method, endpoint, merged_options)

        if response.status_code == 401 and not _retrying:
            logger.warning(
                f"Got 401 from Google API for user={user_id}; refreshing token and retrying once"
            )
            await self.refetch_credentials(user_id)
            return await self.handle(method, endpoint, user_id, options, _retrying=True)

        # if response.status_code == 401:
        #     raise GoogleAuthenticationError(
        #         f"Google API request to {endpoint} still unauthorized after token refresh"
        #     )

        # if response.status_code == 429:
        #     retry_after = response.headers.get("Retry-After")
        #     raise GoogleRateLimitError(
        #         f"Rate limited by Google API on {endpoint}",
        #         retry_after=float(retry_after) if retry_after else None,
        #     )

        # if response.status_code >= 400:
        #     try:
        #         payload = response.json()
        #     except Exception:
        #         payload = response.text
        #     logger.error(
        #         f"Google API error {response.status_code} on {endpoint}: {payload}"
        #     )
        #     raise GoogleAPIRequestError(
        #         f"Google API request to {endpoint} failed with status {response.status_code}",
        #         status_code=response.status_code,
        #         payload=payload,
        #     )

        return response

    async def refetch_credentials(self, user_id: str) -> CredentialsModel:
        """Refetch the credentials, save in the database using CredentialsManager and return the CredentialsModel."""
        credentials = await self._creds_manager.get_credentials(user_id, self.service)

        refresh_token: str | None = getattr(credentials, "refresh_token", None)

        if not refresh_token:
            raise CredentialsRevokedError(
                f"No refresh token stored for user={user_id}; user must re-authorize Google access"
            )

        body = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CONFIG.GOOGLE_CLIENT_ID,
            "client_secret": CONFIG.GOOGLE_CLIENT_SECRET,
        }

        response = await self._api_client.request(
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
        

        if response.status_code != 200:
            try:
                error_payload = response.json()
            except Exception:
                error_payload = {"error": response.text}

            error_code = error_payload.get("error")
            logger.error(f"Token refresh failed for user={user_id}: {error_payload}")

            if error_code in ("invalid_grant", "unauthorized_client"):
                raise CredentialsRevokedError(
                    f"Google refresh token for user={user_id} was revoked or expired; "
                    "user must re-authorize"
                )
            raise Exception(
                f"Google token refresh failed for user={user_id}: {error_payload}"
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
