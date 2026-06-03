from src.db.models import NodesRegistry
from src.workflows.types import ApplicationNode
from typing import List, Optional


class NodeRegistryRepository:
    async def delete_all(self):
        await NodesRegistry.find_all().delete()
        return None

    async def create_new_node(self, node: ApplicationNode) -> NodesRegistry | None:
        node: NodesRegistry | None = await NodesRegistry.insert_one(
            NodesRegistry(
                name=node.name,
                description=node.description,
                type=node.type,
                fn_key=node.key,
                input_model=node.node_input_model.model_json_schema(),
                output_model=node.node_output_model.model_json_schema(),
            )
        )
        return node

    async def create_nodes(self, nodes: List[ApplicationNode]) -> None:
        nodes_to_register: List[NodesRegistry] = [
            NodesRegistry(
                name=node.name,
                description=node.description,
                type=node.type,
                service=node.service,
                valid_permissions=node.valid_permissions,
                fn_key=node.key,
                input_model=node.node_input_model.model_json_schema(),
                output_model=node.node_output_model.model_json_schema(),
            )
            for node in nodes
        ]
        await NodesRegistry.insert_many(nodes_to_register)
        return None

    async def get_all_nodes(self) -> List[NodesRegistry] | None:
        nodes: List[NodesRegistry] = await NodesRegistry.find_all().to_list()
        return nodes


async def test_initialize_nodes():
    from src.integrations.googlecloud.nodes import (
        LIST_USER_GMAIL_LABELS_NODE,
        GET_SINGLE_GMAIL_LABEL_NODE,
        SEND_EMAIL_NODE,
        DRAFT_EMAIL_NODE,
        CREATE_GOOGLE_SHEET_NODE,
        READ_CELL_VALUES_NODE,
        APPEND_CELL_VALUES_NODE,
        UPDATE_CELL_VALUES_NODE,
    )
    from src.db.mongo_db import MongoClient

    client = MongoClient("mongodb://localhost:27017/")
    await client.get_database("wflow_db")
    await client.init_beanie_odm()

    node_repo = NodeRegistryRepository()
    nodes = await node_repo.create_nodes(
        nodes=[
            LIST_USER_GMAIL_LABELS_NODE,
            GET_SINGLE_GMAIL_LABEL_NODE,
            SEND_EMAIL_NODE,
            DRAFT_EMAIL_NODE,
            CREATE_GOOGLE_SHEET_NODE,
            READ_CELL_VALUES_NODE,
            APPEND_CELL_VALUES_NODE,
            UPDATE_CELL_VALUES_NODE,
        ]
    )
    print("Saved nodes are : ", nodes)


if __name__ == "__main__":
    import asyncio as aio

    aio.run(test_initialize_nodes())
