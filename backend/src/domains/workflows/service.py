from src.domains.workflows.repository import WorkflowRepository, NodeRegistryRepository
from src.domains.users.repository import UserRepository
from src.domains.workflows.schema import (
    CreateNewWorkflowModel,
    WorkflowListItemModel,
    PaginationMetadata,
    PaginatedWorkflowsResponse,
    NodesRegistryListItemModel,
    PaginatedNodesResponse,
    SingleWorkflowResponseModel,
    NodeFullResponse,
)
from src.db.postgres.schemas import Workflows, WorkflowsStars, NodesRegistry
from src.workflows.types import NodesTypeEnum
from src.workflows.nodes import NODES_MAP
from src.core.response import AppError
from src.domains.workflows.exceptions import (
    WorkflowNotFoundError,
    WorkflowAlreadyStarredError,
    CannotAccessPrivateWorkflowError,
)

from loguru import logger
from fastapi import HTTPException, status
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio.session import AsyncSession


class WorkflowService:
    def __init__(self):
        self._user_repo = UserRepository()
        self._workflow_repo = WorkflowRepository()
        self._node_registry_repo = NodeRegistryRepository()

    async def update_node_registry(self, session: AsyncSession):
        await self._node_registry_repo.delete_all(session=session)
        await self._node_registry_repo.create_nodes(
            session=session, nodes=NODES_MAP.values()
        )

    # async def create_new_workflow_run(
    #     self, session: AsyncSession, workflow_id: str, user_id: str
    # ) -> Tuple[Workflows, WorkflowRuns]:

    #     workflow = await self._workflow_repo.get_workflow_by_id(workflow_id)
    #     if workflow is None:
    #         raise AppError(WorkflowNotFoundError(data=None))

    #     workflow_run: WorkflowRuns | None = (
    #         await self._workflow_repo.create_worflow_run(
    #             workflow_id=workflow_id, user_id=user_id
    #         )
    #     )

    #     if workflow_run is None:
    #         raise PyMongoError("Result None during normal insert_one operation.")

    #     return workflow, workflow_run

    async def create_new_workflow(
        self, session: AsyncSession, workflow: CreateNewWorkflowModel, user_id: str
    ) -> Workflows:

        new_workflow = await self._workflow_repo.create_workflow(
            session=session,
            user_id=user_id,
            name=workflow.name,
            description=workflow.description,
            nodes=workflow.nodes,
            edges=workflow.edges,
            visibility=workflow.visibility,
        )
        return new_workflow

    async def star_workflow(
        self, session: AsyncSession, workflow_id: str, user_id: str
    ) -> Workflows:
        workflow = await self._workflow_repo.get_workflow_by_id(
            session=session, workflow_id=workflow_id
        )
        if workflow is None:
            raise AppError(WorkflowNotFoundError(data=None))

        workflow = await self._workflow_repo.star_workflow(
            session=session, workflow=workflow, user_id=user_id
        )
        if workflow is None:
            raise AppError(WorkflowAlreadyStarredError(data=None))

        return workflow

    async def _attach_node_schemas(
        self, session: AsyncSession, workflow: SingleWorkflowResponseModel
    ) -> SingleWorkflowResponseModel:
        """Helper to attach input_model and output_model from registry to workflow nodes."""
        for node in workflow.nodes:
            if not node.input_model or not node.output_model:
                registry_item = await self._node_registry_repo.get_node(
                    session=session, fn_key=node.key
                )
                if registry_item:
                    if not node.input_model:
                        node.input_model = registry_item.input_model
                    if not node.output_model:
                        node.output_model = registry_item.output_model
        return workflow

    async def get_workflow_data(
        self, session: AsyncSession, workflow_id: str, user_id: str
    ) -> SingleWorkflowResponseModel:
        workflow: Workflows = await self._workflow_repo.get_workflow_by_id(
            session=session, workflow_id=workflow_id
        )
        if not workflow:
            raise AppError(WorkflowNotFoundError(data=None))

        if workflow.visibility == "private" and str(workflow.created_by) != user_id:
            raise AppError(CannotAccessPrivateWorkflowError(data=None))

        logger.info(f"THe workflow is : {workflow}")

        workflow_data = SingleWorkflowResponseModel(
            workflow_id=str(workflow.id),
            name=workflow.name,
            description=workflow.description,
            nodes=[
                NodeFullResponse(
                    key=node.get("key", ""),
                    name=node.get("name", ""),
                    type=node.get("type", "").upper(),
                    inputs=node.get("inputs", {}),
                    config=node.get("config", {}),
                    outputs=node.get("ouputs", {}),
                )
                for node in workflow.nodes
            ],
            edges=workflow.edges,
            visibility=workflow.visibility,
            stars=workflow.stars,
            created_by=user_id,
        )
        await self._attach_node_schemas(session=session, workflow=workflow_data)
        return workflow_data

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
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        user_id: str | None = None,
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

        workflows, total = await self._workflow_repo.get_workflows(
            session=session,
            projection_model=WorkflowListItemModel,
            page=page,
            page_size=page_size,
            user_id=user_id,
        )

        pagination = self._create_pagination_metadata(total, page, page_size)

        return PaginatedWorkflowsResponse(data=workflows, pagination=pagination)

    async def search_workflows(
        self,
        session: AsyncSession,
        query: str,
        page: int = 1,
        page_size: int = 10,
        user_id: str | None = None,
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

        workflows, total = await self._workflow_repo.get_workflows(
            session=session,
            projection_model=WorkflowListItemModel,
            query=query.strip(),
            page=page,
            page_size=page_size,
            user_id=user_id,
        )
        pagination = self._create_pagination_metadata(total, page, page_size)
        return PaginatedWorkflowsResponse(data=workflows, pagination=pagination)

    async def get_all_nodes(self, session: AsyncSession, page: int, page_size: int):
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10

        nodes, total = await self._node_registry_repo.get_all_nodes(
            session=session, page=page, page_size=page_size
        )

        formatted_nodes = [self._format_node_list_item(node) for node in nodes]
        pagination = self._create_pagination_metadata(total, page, page_size)

        return PaginatedNodesResponse(data=formatted_nodes, pagination=pagination)

    async def get_nodes_by_type_and_service(
        self,
        session: AsyncSession,
        node_type: NodesTypeEnum,
        page: int,
        page_size: int,
        service: Optional[str] = None,
    ):
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10

        nodes, total = await self._node_registry_repo.search_nodes_by_type_and_service(session=session,
            node_type=node_type, service=service, page=page, page_size=page_size
        )

        formatted_nodes = [self._format_node_list_item(node) for node in nodes]
        pagination = self._create_pagination_metadata(total, page, page_size)

        return PaginatedNodesResponse(data=formatted_nodes, pagination=pagination)
