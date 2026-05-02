from src.config import CONFIG
from src.integrations.pinecone_db.constants import PINECONE_INDEX_NAME

from pinecone import PineconeAsyncio
from pinecone.db_data.index_asyncio import _IndexAsyncio
from pinecone.exceptions.exceptions import PineconeApiException
from typing import  Dict, Generator, Optional
from loguru import logger
from itertools import islice


class PineconeClient:
    """Provides async interface for interacting with pinecone vector database."""

    def __init__(self, client: PineconeAsyncio, index: _IndexAsyncio):
        self._client: PineconeAsyncio | None = client
        self._index: _IndexAsyncio | None = index

    @classmethod
    async def create(cls, index_name: str, api_key: str, host: str):
        """Creates new pinecone client with new asyncio client and index."""
        client = PineconeAsyncio(api_key=api_key)

        if not await client.has_index(index_name):
            await client.create_index_for_model(
                name=index_name,
                cloud="aws",
                region="us-east-1",
                embed={
                    "model": "llama-text-embed-v2",
                    "field_map": {"text": "title", "dimension": 2048},
                },
            )
        index = client.IndexAsyncio(host=host)
        return cls(client, index)

    async def aclose(self) -> None:
        await self._index.close()
        await self._client.close()
        self._index = None
        self._client = None

    async def does_namespaces_exist(self) -> bool:
        logger.info("Checking for data in pinecone.")
        stats = await self._index.describe_index_stats()
        namespaces = stats["namespaces"]
        return True if len(namespaces) > 0 else False

    async def get_relevant_chunks(
        self,
        query: str,
        user_id: str,
        requested_fields: list[str],
        metadata: dict[str, str] = None,
        k: int = 10,
    ) -> dict[str, str | float]:

        try:
            result = await self._index.search(
                namespace=user_id,
                query={
                    "inputs": {"text": f"{query}"},
                    "top_k": k,
                },
                fields=requested_fields,
            )
            hits = result.get("result", {}).get("hits", [])

            return hits

        except PineconeApiException as exc:
            raise exc
        except Exception as e:
            raise e

    async def upsert_records(
        self,
        records: list,
        namespace: str,
        metadatas: dict[str, str] = None,
    ):
        try:

            def chunks(
                iterable: list[Dict], size=96
            ) -> Generator[list[Dict], None, None]:
                """This function helps to divide the list into given size or less"""
                iterator = iter(iterable)
                for first in iterator:
                    yield [first] + list(islice(iterator, size - 1))

            for batch in chunks(records, 96):
                logger.debug(f"The batch is : {batch} \n\n")
                await self._index.upsert_records(
                    namespace=namespace,
                    records=batch,
                )
            logger.info(f"Upserted {len(records)} records to pinecone")

        except PineconeApiException as e:
            raise e
        except Exception as e:
            raise e


async def init_pinecone_db_async():
    return await PineconeClient.create(
        index_name=PINECONE_INDEX_NAME,
        api_key=CONFIG.PINECONE_API_KEY,
        host=CONFIG.PINECONE_HOST,
    )


if __name__ == "__main__":
    import asyncio as aio

    async def main():
        pinecone_client = await init_pinecone_db_async()
        print(pinecone_client)

    aio.run(main())
