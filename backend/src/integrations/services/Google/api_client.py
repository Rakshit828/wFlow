import httpx
from typing import Tuple, Any, Dict
from loguru import logger

from src.integrations.services.Google import (
    CredentialsModel,
    SERVICE_THAT_SHOULD_BE_REPLACED_BY_IN_BASE_URL,
)
from src.integrations.services.Google import GoogleErrorStatus, GoogleApiErrorResponse
from src.integrations.interfaces.service_api_client import ServiceApiClientInterface


class GoogleAPIClient(ServiceApiClientInterface):
    def __init__(
        self,
        credentials: CredentialsModel,
        service: str,
        req_timeout: float = 30.0,
        base_url: str = "https://www.googleapis.com",
        **kwargs,
    ):
        self.__client = httpx.AsyncClient(timeout=req_timeout, **kwargs)
        self.__credentials: CredentialsModel = credentials
        self.base_url = (
            base_url.replace("www", service)
            if service in SERVICE_THAT_SHOULD_BE_REPLACED_BY_IN_BASE_URL
            else base_url
        )

    def service(self) -> str:
        return "GOOGLE"

    def _set_authorization_header(self, headers: dict) -> None:
        headers["Authorization"] = f"Bearer {self.__credentials.access_token}"
        return headers

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
    ) -> Tuple[httpx.Response, dict[str, Any]]:

        if requires_bearer_token:
            headers = kwargs.get("headers", {})

            if not is_refresh:
                headers = self._set_authorization_header(headers)

            kwargs["headers"] = headers

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
                    raise Exception("Refresh token has also been expired.")

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

        return response, json_response


    async def close(self):
        await self.__client.aclose()
