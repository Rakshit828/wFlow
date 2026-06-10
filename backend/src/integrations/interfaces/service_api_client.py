from abc import ABC, abstractmethod
from typing import Any


class ServiceApiClientInterface(ABC):

    @abstractmethod
    async def request(self) -> Any:
        pass

    @property
    @abstractmethod
    def service(self) -> str:
        pass
