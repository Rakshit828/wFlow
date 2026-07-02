from datetime import datetime, timedelta, timezone
import httpx
from loguru import logger
from src.integrations.components.service_client import ServiceRequestHandler
from src.integrations.components.api_client import ApiClient
from src.integrations.components.credentials import CredentialsManager
from src.integrations.components.api_client import RequestOptions


class GoogleRequestHandler(ServiceRequestHandler):
 
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    GMAIL_BASE_URL = "https://gmail.googleapis.com/gmail/v1"
    DRIVE_BASE_URL = "https://www.googleapis.com/drive/v3"
 
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
        try:
            credentials = await self._creds_manager.get_credentials(user_id, self.service)
        except CredentialsNotFoundError:
            raise
 
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
 
        if response.status_code == 401:
            raise GoogleAuthenticationError(
                f"Google API request to {endpoint} still unauthorized after token refresh"
            )
 
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise GoogleRateLimitError(
                f"Rate limited by Google API on {endpoint}",
                retry_after=float(retry_after) if retry_after else None,
            )
 
        if response.status_code >= 400:
            try:
                payload = response.json()
            except Exception:
                payload = response.text
            logger.error(f"Google API error {response.status_code} on {endpoint}: {payload}")
            raise GoogleAPIRequestError(
                f"Google API request to {endpoint} failed with status {response.status_code}",
                status_code=response.status_code,
                payload=payload,
            )
 
        return response
 
    # ------------------------------------------------------------------ #
    # Token refresh
    # ------------------------------------------------------------------ #
 
    async def refetch_credentials(self, user_id: str) -> CredentialsModel:
        credentials = await self._creds_manager.get_credentials(user_id, self.service)
 
        refresh_token = getattr(credentials, "refresh_token", None)
        client_id = getattr(credentials, "client_id", None)
        client_secret = getattr(credentials, "client_secret", None)
 
        if not refresh_token:
            raise CredentialsRevokedError(
                f"No refresh token stored for user={user_id}; user must re-authorize Google access"
            )
 
        body = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
 
        try:
            response = await self._api_client.request(
                "POST",
                self.TOKEN_URL,
                {
                    "data": body,
                    "json": None,
                    "params": None,
                    "headers": {"Content-Type": "application/x-www-form-urlencoded"},
                    "timeout": 15,
                },
                is_refresh=True,
            )
        except GoogleAPIConnectionError as exc:
            raise TokenRefreshError(
                f"Network error refreshing Google token for user={user_id}"
            ) from exc
 
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
            raise TokenRefreshError(
                f"Google token refresh failed for user={user_id}: {error_payload}"
            )
 
        token_data = response.json()
        new_access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)
 
        if not new_access_token:
            raise TokenRefreshError(
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
 
        new_credentials = self._creds_manager.credentials_model.model_validate(updated_data)
        await self._creds_manager.update_credentials(user_id, self.service, new_credentials)
        return new_credentials
 
    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
 
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
 
    # ------------------------------------------------------------------ #
    # Convenience wrappers for Gmail / Drive
    # ------------------------------------------------------------------ #
 
    async def list_gmail_messages(
        self, user_id: str, query: str | None = None, max_results: int = 25
    ) -> Dict[str, Any]:
        params: Dict[str, str] = {"maxResults": str(max_results)}
        if query:
            params["q"] = query
        response = await self.handle(
            "GET",
            f"{self.GMAIL_BASE_URL}/users/me/messages",
            user_id,
            {"data": None, "json": None, "params": params, "headers": None, "timeout": None},
        )
        return response.json()
 
    async def list_drive_files(
        self, user_id: str, query: str | None = None, page_size: int = 25
    ) -> Dict[str, Any]:
        params: Dict[str, str] = {"pageSize": str(page_size)}
        if query:
            params["q"] = query
        response = await self.handle(
            "GET",
            f"{self.DRIVE_BASE_URL}/files",
            user_id,
            {"data": None, "json": None, "params": params, "headers": None, "timeout": None},
        )
        return response.json()
 