from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.asynchronous.collection import AsyncCollection
import asyncio as aio
import beanie
from typing import Sequence

from src.db.models import Users, AppIntegrations, OAuthAccounts, NodesRegistry


class MongoClient:
    def __init__(self, db_uri: str):
        self._client: AsyncMongoClient = AsyncMongoClient(db_uri)
        self.db: AsyncDatabase | None = None

    def get_client(self) -> AsyncMongoClient:
        return self._client

    async def get_database(self, db_name: str) -> AsyncDatabase:
        """Returns the given mongodb database or creates and returns if doesn't exist."""
        self.db = self._client.get_database(db_name)
        return self.db

    async def get_collection(self, collection_name: str) -> AsyncCollection:
        if self.db is not None:
            if collection_name not in (await self.db.list_collection_names()):
                return await self.db.create_collection(collection_name)
            return self.db[collection_name]

        raise TypeError("Create a database first.")

    async def init_beanie_odm(
        self, models: Sequence[beanie.Document] | None = None
    ) -> None:
        if models is None:
            models = [Users, AppIntegrations, OAuthAccounts, NodesRegistry]
        await beanie.init_beanie(database=self.db, document_models=models)
        return


async def main():
    mongo = MongoClient("mongodb://localhost:27017/")
    db = await mongo.get_database("wflow_db")
    collec = await mongo.get_collection("nodes")
    print("Collec is : ", collec)


if __name__ == "__main__":
    aio.run(main())
