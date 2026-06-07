import re
from typing import Tuple, Optional, List, Type, TypeVar
from beanie import PydanticObjectId
from loguru import logger
from bson import ObjectId
from pydantic import BaseModel

from src.domains.workflows.models import Workflows, NodesRegistry, WorkflowRuns
from src.workflows.types import ApplicationNode, NodesTypeEnum


ProjectionModelT = TypeVar("ProjectionModelT", bound=BaseModel)


class WorkflowRepository:
    def __init__(self):
        pass

    async def create_worflow_run(self, workflow_id: str, user_id: str) -> WorkflowRuns | None:
        doc = WorkflowRuns(
            workflow_id=PydanticObjectId(workflow_id), user_id=PydanticObjectId(user_id)
        )
        return await WorkflowRuns.insert_one(doc)

    async def get_workflow_by_id(self, workflow_id: str) -> Workflows | None:
        # Beanie automatically handles string-to-ObjectId conversion if you pass a string to .get()
        return await Workflows.get(workflow_id)

    async def get_workflows(
        self,
        projection_model: Type[ProjectionModelT],
        page: int = 1,
        page_size: int = 10,
        user_id: str | None = None,
        query: str | None = None,
    ) -> Tuple[List[ProjectionModelT], int]:
        skip = (page - 1) * page_size

        proj_model = {}
        for field, _ in projection_model.model_fields.items():
            if field == "workflow_id":
                proj_model["_id"] = 0
                proj_model["workflow_id"] = "$_id"
                # Map MongoDB's _id to workflow_id
            elif field == "created_by":
                proj_model["created_by"] = (
                    "$user.username"  # Extract username from joined user
                )
            else:
                proj_model[field] = 1

        if "created_by" not in projection_model.model_fields:
            raise Exception("created_by is required in projection field.")

        logger.debug(f"The projection model is : {proj_model}")

        match_filters = {"visibility": "public"}
        if user_id is not None:
            match_filters["created_by"] = ObjectId(user_id)
            match_filters.pop("visibility")

        if query is not None:
            pattern = re.compile(query, re.IGNORECASE)
            match_filters["name"] = {"$regex": pattern}

        result = await Workflows.aggregate(
            [
                {"$match": match_filters},
                {
                    "$facet": {
                        "workflows": [
                            {
                                "$lookup": {
                                    "from": "Users",
                                    "localField": "created_by",
                                    "foreignField": "_id",
                                    "as": "user",
                                }
                            },
                            {
                                "$unwind": {
                                    "path": "$user",
                                    "preserveNullAndEmptyArrays": True,
                                }
                            },
                            {"$project": proj_model},
                            {"$skip": skip},
                            {"$limit": page_size},
                        ],
                        "total": [{"$count": "count"}],
                    }
                },
            ]
        ).to_list()

        data = result[0]
        workflows = data["workflows"]
        total = data["total"][0]["count"] if data["total"] else 0

        logger.info(f"The workflows are : {workflows}")
        proj_workflows = [projection_model(**wf) for wf in workflows]
        return proj_workflows, total

    async def search_nodes_by_type_and_service(
        self,
        node_type: NodesTypeEnum,
        service: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[NodesRegistry], int]:

        skip = (page - 1) * page_size

        if service is not None:
            pattern = re.compile(service, re.IGNORECASE)

        search_query = NodesRegistry.find(NodesRegistry.type == node_type)

        if service is not None:
            search_query = search_query.find(
                NodesRegistry.service == pattern, Workflows.visibility == "public"
            )

        total = await search_query.count()
        nodes = await search_query.skip(skip).limit(page_size).to_list()

        return nodes, total


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


