from abc import ABC, abstractmethod
from src.integrations.components.api_client import ApiClient
from src.integrations.components.credentials import CredentialsManager
import httpx
from .types import RequestOptions, CredentialsModel
from typing import Any


class ServiceRequestHandler(ABC):
    _api_client: ApiClient
    _creds_manager: CredentialsManager
    _obj: "ServiceRequestHandler | None" = None

    def __init__(
        self, api_client: ApiClient, creds_manager: CredentialsManager
    ) -> None:
        self._api_client = api_client
        self._creds_manager = creds_manager

    @classmethod
    def get(
        cls, api_client: ApiClient | None, creds_manager: CredentialsManager | None
    ) -> "ServiceRequestHandler":
        if not cls._obj and not (api_client and creds_manager):
            raise Exception(
                "Must pass in api_client and creds_manager when first creating it."
            )
        if cls._obj:
            return cls._obj

        if api_client and creds_manager:
            return cls(api_client, creds_manager)

        raise Exception("Impossible situation")

    @abstractmethod
    async def handle(
        self,
        method: str,
        endpoint: str,
        options: RequestOptions | None = None,
    ) -> tuple[httpx.Response, dict[str, Any]]: ...

    @abstractmethod
    async def refetch_credentials(self, user_id: str) -> CredentialsModel: ...

    @property
    @abstractmethod
    def service(self) -> str: ...
