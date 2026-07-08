from typing import Any, Dict
from loguru import logger
import httpx
from .exceptions import ApiConnectionError
from .types import RequestOptions


class ApiClient:

    def __init__(self, base_url: str):
        self.__client = httpx.AsyncClient()
        self._base_url: str = base_url.rstrip("/")

    def _resolve_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{self._base_url}/{endpoint.lstrip('/')}"

    def _safe_parse_json(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except Exception as e:
            raise e

    async def request(
        self,
        method: str,
        endpoint: str,
        options: RequestOptions | None = None,
        is_refresh: bool = False,
        is_retry: bool = False,
    ) -> tuple[httpx.Response, Dict[str, Any]]:
        url = self._resolve_url(endpoint)
        logger.info(f"Request to: {url} (refresh={is_refresh}, retry={is_retry})")

        req_data: Dict[str, Any] = {"method": method, "url": url}
        if options:
            for key, value in options.items():
                if value is not None:
                    req_data[key] = value
        req_data.setdefault("timeout", 30)

        try:
            response = await self.__client.request(**req_data)
            return response, self._safe_parse_json(response)
        
        except httpx.TimeoutException as exc:
            logger.error(f"Timeout calling {url}: {exc}")
            raise ApiConnectionError(f"Timed out calling {url}") from exc
        except httpx.ConnectError as exc:
            logger.error(f"Connection error calling {url}: {exc}")
            raise ApiConnectionError(f"Could not connect to {url}") from exc
        except httpx.HTTPError as exc:
            logger.error(f"HTTP error calling {url}: {exc}")
            raise ApiConnectionError(f"HTTP error calling {url}: {exc}") from exc

    async def close(self):
        await self.__client.aclose()
