from typing import Any, Dict
from loguru import logger
import httpx
from .exceptions import ConnectionError
from .types import RequestOptions

class ApiClient:

    def __init__(self, base_url: str):
        self.__client = httpx.AsyncClient()
        self._base_url: str = base_url.rstrip("/")

    def _resolve_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{self._base_url}/{endpoint.lstrip('/')}"

    async def request(
        self,
        method: str,
        endpoint: str,
        options: RequestOptions | None = None,
        is_refresh: bool = False,
        is_retry: bool = False,
    ) -> httpx.Response:
        url = self._resolve_url(endpoint)
        logger.info(f"Request to: {url} (refresh={is_refresh}, retry={is_retry})")

        req_data: Dict[str, Any] = {"method": method, "url": url}
        if options:
            for key, value in options.items():
                if value is not None:
                    req_data[key] = value
        req_data.setdefault("timeout", 30)

        try:
            return await self.__client.request(**req_data)
        except httpx.TimeoutException as exc:
            logger.error(f"Timeout calling {url}: {exc}")
            raise ConnectionError(f"Timed out calling {url}") from exc
        except httpx.ConnectError as exc:
            logger.error(f"Connection error calling {url}: {exc}")
            raise ConnectionError(f"Could not connect to {url}") from exc
        except httpx.HTTPError as exc:
            logger.error(f"HTTP error calling {url}: {exc}")
            raise ConnectionError(f"HTTP error calling {url}: {exc}") from exc

    async def close(self):
        await self.__client.aclose()
