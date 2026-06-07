from temporalio import client
from src.config import CONFIG
from asyncio import Lock


class TemporalClientManager:
    _client: client.Client | None = None
    _lock: Lock = Lock()

    @classmethod
    async def get_client(cls) -> client.Client:
        if cls._client is None:
            async with cls._lock:
                if cls._client is None:
                    cls._client = await client.Client.connect(CONFIG.TEMPORAL_URL)

        return cls._client
