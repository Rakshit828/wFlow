from abc import ABC, abstractmethod
from src.integrations.components.api_client import ApiClient
from src.integrations.components.credentials import CredentialsManager
import httpx
from .types import RequestOptions, CredentialsModel


class ServiceRequestHandler(ABC):

    def __init__(
        self, api_client: ApiClient, creds_manager: CredentialsManager
    ) -> None:
        self._api_client = api_client
        self._creds_manager = creds_manager

    @abstractmethod
    async def handle(
        self,
        method: str,
        endpoint: str,
        user_id: str,
        options: RequestOptions | None = None,
    ) -> httpx.Response: ...

    @abstractmethod
    async def refetch_credentials(self, user_id: str) -> CredentialsModel: ...

    @property
    @abstractmethod
    def service(self) -> str: ...
