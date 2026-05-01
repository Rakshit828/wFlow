import httpx
from typing import Tuple, Any, Dict
from datetime import datetime, timedelta
from loguru import logger

from src.config import CONFIG
from src.integrations.googlecloud import CredentialsModel
from src.integrations.googlecloud import GoogleErrorStatus, GoogleApiErrorResponse
from src.repositories.app_integrations import AppIntegrationsRepository


class GoogleAPIClient:
    def __init__(
        self,
        credentials: CredentialsModel,
        service: str,
        integration_repo: AppIntegrationsRepository,
        req_timeout: float = 30.0,
        base_url: str = "https://www.googleapis.com",
        **kwargs,
    ):
        self.__client = httpx.AsyncClient(timeout=req_timeout, **kwargs)
        self.__integration_repo: AppIntegrationsRepository = integration_repo
        self.__credentials: CredentialsModel = credentials
        self.base_url = base_url.replace("www", service)

    def _set_authorization_header(self, headers: dict) -> None:
        headers["Authorization"] = f"Bearer {self.__credentials.access_token}"
        return headers

    async def do_refresh_actions(self):
        data = {
            "client_id": self.__credentials.client_id,
            "client_secret": self.__credentials.client_secret,
            "refresh_token": self.__credentials.refresh_token,
            "grant_type": "refresh_token",
        }
        response, json_response = await self.request(
            "POST",
            CONFIG.GOOGLE_TOKEN_URL,
            requires_bearer_token=False,
            use_base_url=False,
            data=data,
        )

        if response.status_code == 200:
            logger.info(f"REfresh response is : {json_response}")
            now = datetime.now()
            self.__credentials.access_token = json_response["access_token"]
            self.__credentials.access_token_expiry = (
                timedelta(seconds=int(json_response["expires_in"])) + now
            )
            self.__credentials.refresh_token_expiry = (
                timedelta(seconds=int(json_response["refresh_token_expires_in"])) + now
            )
            update_response = await self.__integration_repo.update_credentials(
                integration_id=self.__credentials.integration_id,
                access_token=self.__credentials.access_token,
                access_token_expiry=self.__credentials.access_token_expiry,
                refresh_token_expiry=self.__credentials.refresh_token_expiry,
            )

            logger.info(f"Tokens refreshed and updated successfully {update_response}.")

    def _safe_json(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except Exception:
            return {}

    async def request(
        self,
        method: str,
        endpoint: str,
        requires_bearer_token: bool,
        use_base_url: str = True,
        is_refresh: bool = False,
        is_retried_call: bool = False,
        **kwargs,
    ) -> Tuple[httpx.Response, dict]:

        if requires_bearer_token:
            kwargs["headers"] = {}

            if not is_refresh:
                kwargs["headers"] = self._set_authorization_header(kwargs["headers"])

        url = f"{self.base_url}/{endpoint.lstrip('/')}" if use_base_url else endpoint
        response = await self.__client.request(method, url, **kwargs)

        json_response = self._safe_json(response)

        logger.info(f"Requested url is : {response.url}")

        if response.is_error:
            json_error_body: GoogleApiErrorResponse = json_response.get("error")
            logger.error(response)
            if (
                response.status_code == 401
                and requires_bearer_token
                and json_error_body["status"] == GoogleErrorStatus.UNAUTHENTICATED
            ):
                if is_retried_call:
                    raise Exception("Impossible event.")

                logger.info(f"Performing refresh.")
                await self.do_refresh_actions()
                response, json_response = await self.request(
                    method,
                    endpoint,
                    requires_bearer_token,
                    is_retried_call=True,
                    **kwargs,
                )
                return response, json_response

            elif (
                response.status_code == 401
                and is_refresh
                and json_error_body["status"] == GoogleErrorStatus.UNAUTHENTICATED
            ):
                logger.error(f"Your refresh token has been expired too. Please retry.")
                raise Exception(
                    "Your refresh token has been expired too. Please retry."
                )
            elif (
                response.status_code == 403
                and json_error_body["status"] == GoogleErrorStatus.PERMISSION_DENIED
            ):
                logger.error(
                    f"Current access token has not enough permissions for this action.\n {json_error_body}"
                )
                raise Exception(json_error_body["message"])

            elif response.status_code == 404 and json_error_body is None:
                logger.error(f"Url: {url} not found.")
                raise Exception("Resource/URL not found.")

            else:
                logger.error(f"Error.\n {json_error_body}")
                raise Exception(json_error_body["message"])

        return response, json_response

    async def close(self):
        await self.__client.aclose()
