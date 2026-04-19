from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    async def stream(self):
        pass

    @abstractmethod
    async def inference(self):
        pass