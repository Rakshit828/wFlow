from src.repositories.workflows import WorkflowRepository
from src.repositories.auth_repository import UserRepository
from src.schemas.workflow import (
    CreateNewWorkflowModel,
    WorkflowListItemModel,
    PaginationMetadata,
    PaginatedWorkflowsResponse,
    NodesRegistryListItemModel,
    PaginatedNodesResponse,
)
from src.db.models import Users, Workflows, WorkflowsStars, NodesRegistry
from beanie.odm.operators.update.general import Set
from beanie.operators import Inc
from loguru import logger
from beanie.odm.queries.update import UpdateResponse
from pymongo.results import UpdateResult
from beanie import PydanticObjectId
from fastapi import HTTPException, status
from typing import Optional
from src.workflows.types import NodesTypeEnum, ApplicationNode


class WorkflowService:
    def __init__(self):
        self._user_repo = UserRepository()
        self._workflow_repo = WorkflowRepository()

    async def load_from_node_registry(self):
        pass

    async def star_workflow(self, workflow_id: str, user_id: str) -> Workflows | None:
        wf_id_obj = PydanticObjectId(workflow_id)
        user_id_obj = PydanticObjectId(user_id)

        result: UpdateResult = await WorkflowsStars.find_one(
            WorkflowsStars.workflow_id == wf_id_obj,
            WorkflowsStars.user_id == user_id_obj,
        ).update(
            {
                "$setOnInsert": {
                    "workflow_id": wf_id_obj,
                    "user_id": user_id_obj,
                }
            },
            upsert=True,
        )

        if result.upserted_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow already starred by this user",
            )

        updated_workflow = await Workflows.find_one(Workflows.id == wf_id_obj).update(
            Inc({Workflows.stars: 1}), response_type=UpdateResponse.NEW_DOCUMENT
        )

        if not updated_workflow:
            await WorkflowsStars.find_one(
                WorkflowsStars.workflow_id == wf_id_obj,
                WorkflowsStars.user_id == user_id_obj,
            ).delete()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
            )

        return updated_workflow

    async def create_new_workflow(self, workflow: CreateNewWorkflowModel, user_id: str):
        user: Users | None = await self._user_repo.get_user_by_id(user_id=user_id)

        if not user:
            raise Exception("User not found")

        doc: Workflows = Workflows(
            name=workflow.name,
            description=workflow.description,
            nodes=workflow.nodes,
            edges=workflow.edges,
            visibility=workflow.visibility,
            created_by=user.id,
        )
        new_workflow = await Workflows.insert_one(doc)

        return new_workflow

    def _format_workflow_list_item(self, workflow: Workflows) -> WorkflowListItemModel:
        """Convert Workflows document to WorkflowListItemModel."""
        return WorkflowListItemModel(
            workflow_id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            visibility=workflow.visibility,
            stars=workflow.stars,
            created_by=str(workflow.created_by),
        )

    def _format_node_list_item(self, node: NodesRegistry) -> NodesRegistryListItemModel:
        return NodesRegistryListItemModel(
            node_id=str(node.id),
            name=node.name,
            description=node.description,
            type=node.type,
            service=node.service,
            valid_permissions=node.valid_permissions,
            fn_key=node.fn_key,
            input_model=node.input_model,
            output_model=node.output_model,
        )

    def _create_pagination_metadata(
        self, total: int, page: int, page_size: int
    ) -> PaginationMetadata:
        """Create pagination metadata."""
        total_pages = (total + page_size - 1) // page_size
        return PaginationMetadata(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

    async def get_all_workflows(
        self, page: int = 1, page_size: int = 10
    ) -> PaginatedWorkflowsResponse:
        """
        Fetch all workflows with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            PaginatedWorkflowsResponse with workflows and pagination metadata
        """
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10

        workflows, total = await self._workflow_repo.get_all_workflows(
            page=page, page_size=page_size
        )

        formatted_workflows = [self._format_workflow_list_item(wf) for wf in workflows]
        pagination = self._create_pagination_metadata(total, page, page_size)

        return PaginatedWorkflowsResponse(
            data=formatted_workflows, pagination=pagination
        )

    async def search_workflows(
        self, query: str, page: int = 1, page_size: int = 10
    ) -> PaginatedWorkflowsResponse:
        """
        Search workflows by name with pagination.

        Args:
            query: Search query string
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            PaginatedWorkflowsResponse with matching workflows and pagination metadata
        """
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10
        if not query or not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty",
            )

        workflows, total = await self._workflow_repo.search_workflows_by_name(
            query=query.strip(), page=page, page_size=page_size
        )

        formatted_workflows = [self._format_workflow_list_item(wf) for wf in workflows]
        pagination = self._create_pagination_metadata(total, page, page_size)

        return PaginatedWorkflowsResponse(
            data=formatted_workflows, pagination=pagination
        )

    async def get_all_nodes(self, page: int, page_size: int):
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10

        total = await NodesRegistry.find().count()
        nodes = await NodesRegistry.find_all().skip((page - 1) * page_size).limit(page_size).to_list()

        formatted_nodes = [self._format_node_list_item(node) for node in nodes]
        pagination = self._create_pagination_metadata(total, page, page_size)

        return PaginatedNodesResponse(data=formatted_nodes, pagination=pagination)

    async def get_nodes_by_type_and_service(
        self,
        node_type: NodesTypeEnum,
        page: int,
        page_size: int,
        service: Optional[str] = None,
    ):
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10

        nodes, total = await self._workflow_repo.search_nodes_by_type_and_service(
            node_type=node_type, service=service, page=page, page_size=page_size
        )

        formatted_nodes = [self._format_node_list_item(node) for node in nodes]
        pagination = self._create_pagination_metadata(total, page, page_size)

        return PaginatedNodesResponse(data=formatted_nodes, pagination=pagination)
