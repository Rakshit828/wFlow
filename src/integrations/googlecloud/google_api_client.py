import httpx
from typing import Tuple
from src.config import CONFIG

from src.integrations.googlecloud import CredentialsModel
from src.integrations.googlecloud import GoogleErrorStatus
from src.repositories.app_integrations import AppIntegrationsRepository


class GoogleAPIClient:
    def __init__(
        self,
        integration_repo: AppIntegrationsRepository,
        credentials: CredentialsModel,
        req_timeout: float = 30.0,
        **kwargs,
    ):
        self.__client = httpx.AsyncClient(timeout=req_timeout, **kwargs)
        self.credentials: CredentialsModel = credentials
        self.integration_repo = integration_repo

        self.base_url = "https://www.googleapis.com"

    async def perform_refresh(self):
        data = {
            "client_id": CONFIG.GOOGLE_CLIENT_ID,
            "client_secret": CONFIG.GOOGLE_CLIENT_SECRET,
            "refresh_token": self.credentials.refresh_token,
            "grant_type": "refresh_token",
        }
        response, json_response = await self.request(
            method="POST",
            endpoint=CONFIG.GOOGLE_TOKEN_URL,
            requires_bearer_token=False,
            use_base_url=False,
            is_refresh=True,
            data=data,
        )

    async def request(
        self,
        method: str,
        endpoint: str,
        requires_bearer_token: bool,
        use_base_url: str = True,
        is_refresh: bool = False,
        **kwargs,
    ) -> Tuple[httpx.Response, dict]:

        if requires_bearer_token:
            if kwargs.get("headers") is None:
                kwargs["headers"] = {}
            if "Authorization" not in kwargs["headers"]:
                kwargs["headers"][
                    "Authorization"
                ] = f"Bearer {self.credentials.access_token if not is_refresh else self.credentials.refresh_token}"

        url = f"{self.base_url}/{endpoint.lstrip('/')}" if use_base_url else endpoint
        response = await self.__client.request(method, url, **kwargs)
        json_response = response.json()

        if response.is_error:
            if (
                # This is the condition for invalid access_token
                response.status_code == 401
                and requires_bearer_token
                and json_response["error"]["status"]
                == GoogleErrorStatus.UNAUTHENTICATED
            ):
                await self.perform_refresh()

        return response, json_response

    async def close(self):
        await self.__client.aclose()
