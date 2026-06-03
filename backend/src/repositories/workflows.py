import re
from typing import Tuple, Optional, List
from beanie import PydanticObjectId
from src.db.models import Workflows, NodesRegistry
from src.workflows.types import NodesTypeEnum


class WorkflowRepository:
    def __init__(self):
        pass

    async def get_workflow_by_id(self, workflow_id: str) -> Workflows | None:
        # Beanie automatically handles string-to-ObjectId conversion if you pass a string to .get()
        return await Workflows.get(workflow_id)

    async def get_all_workflows(
        self, page: int = 1, page_size: int = 10
    ) -> Tuple[List[Workflows], int]:
        """
        Fetch all workflows with pagination.
        """
        skip = (page - 1) * page_size

        # 1. Initialize the find operation expression once
        query = Workflows.find()

        # 2. Extract total count and paginated List efficiently
        total = await query.count()
        workflows = await query.skip(skip).limit(page_size).to_list()

        return workflows, total

    async def search_workflows_by_name(
        self, query: str, page: int = 1, page_size: int = 10
    ) -> Tuple[List[Workflows], int]:
        """
        Search workflows by name using case-insensitive regex search.
        """
        skip = (page - 1) * page_size

        # FIX: Use Python's native re.compile for case-insensitive ('i') regex tracking
        pattern = re.compile(query, re.IGNORECASE)

        # 1. Initialize the search query expression
        search_query = Workflows.find(Workflows.name == pattern)

        # 2. Resolve both values reusing the same expression object
        total = await search_query.count()
        workflows = await search_query.skip(skip).limit(page_size).to_list()

        return workflows, total

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
            search_query = search_query.find(NodesRegistry.service == pattern)

        total = await search_query.count()
        nodes = await search_query.skip(skip).limit(page_size).to_list()

        return nodes, total
