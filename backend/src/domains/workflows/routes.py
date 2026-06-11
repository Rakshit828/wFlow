from loguru import logger
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from src.domains._shared.dependencies import UserAndSessionData
from src.config import CONFIG
from src.utils.file_uploads import AsyncLocalStorageClient
from src.domains.workflows.types import (
    CreateNewWorkflowModel,
    WorkflowResponseModel,
    StarWorkflowResponseModel,
    PaginatedWorkflowsResponse,
    PaginatedNodesResponse,
    SingleWorkflowResponseModel,
)
from src.domains._shared.dependencies import (
    get_session,
    get_user_and_session,
    UserAndSessionData,
)
from src.workflows.types import NodesTypeEnum, Workflow
from src.domains.workflows.service import WorkflowService
from src.services.temporal_client import TemporalClientManager
from src.workflows.types import WorkflowInput
from temporalio import client
from src.utils.runner import safely_run
from src.services.workflow_streaming import workflow_listener
from src.core.response import SuccessResponse
from src.db.postgres.schemas import Users
from sqlalchemy.ext.asyncio.session import AsyncSession

workflow_router = APIRouter()

internal_storage_client = AsyncLocalStorageClient(
    base_storage_dir=CONFIG.LOCAL_STORAGE_PATH
)


@workflow_router.post("/update-node-registry")
async def update_node_registry(
    session: AsyncSession = Depends(get_session),
    workflow_service: WorkflowService = Depends(WorkflowService),
):
    await workflow_service.update_node_registry(session=session)
    return {"status": "success", "message": "Node registry updated successfully"}


@workflow_router.get(
    "/all-nodes", response_model=SuccessResponse[PaginatedNodesResponse]
)
async def get_all_nodes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    current_user: UserAndSessionData = Depends(get_user_and_session),
    session: AsyncSession = Depends(get_session),
    workflow_service: WorkflowService = Depends(WorkflowService),
) -> SuccessResponse[PaginatedNodesResponse]:
    session = current_user.get_session()
    nodes_data = await workflow_service.get_all_nodes(
        session=session, page=page, page_size=page_size
    )
    return SuccessResponse[PaginatedNodesResponse](data=nodes_data)


@workflow_router.get(
    "/nodes/{node_type}", response_model=SuccessResponse[PaginatedNodesResponse]
)
async def get_all_nodes_by_type_and_service(
    node_type: NodesTypeEnum,
    service: str = Query(None),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    current_user: UserAndSessionData = Depends(get_user_and_session),
    workflow_service: WorkflowService = Depends(WorkflowService),
) -> SuccessResponse[PaginatedNodesResponse]:
    session = current_user.get_session()
    nodes_data = await workflow_service.get_nodes_by_type_and_service(
        session=session,
        node_type=node_type,
        service=service,
        page=page,
        page_size=page_size,
    )
    return SuccessResponse[PaginatedNodesResponse](data=nodes_data)


@workflow_router.get("/", response_model=SuccessResponse[PaginatedWorkflowsResponse])
async def get_all_workflows(
    explore: bool = Query(
        False,
        description="Explore = True means exploring the workflows created in application. explore=False means exploring user created workflows.",
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    workflow_service: WorkflowService = Depends(WorkflowService),
    current_user: UserAndSessionData = Depends(get_user_and_session),
) -> SuccessResponse[PaginatedWorkflowsResponse]:
    """
    Fetch all workflows with pagination.

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Number of items per page, max 100 (default: 10)
    """
    user: Users = current_user.get_user()
    session: AsyncSession = current_user.get_session()

    workflows = await workflow_service.get_all_workflows(
        session=session,
        page=page,
        page_size=page_size,
        user_id=str(user.id) if explore is False else None,
    )
    return SuccessResponse[PaginatedWorkflowsResponse](data=workflows)


@workflow_router.get(
    "/search", response_model=SuccessResponse[PaginatedWorkflowsResponse]
)
async def search_workflows(
    explore: bool = Query(
        False,
        description="Explore = True means exploring the workflows created in application. explore=False means exploring user created workflows.",
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    query: str = Query(..., min_length=1, description="Search query for workflow name"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    workflow_service: WorkflowService = Depends(WorkflowService),
    current_user: UserAndSessionData = Depends(get_user_and_session),
) -> SuccessResponse[PaginatedWorkflowsResponse]:
    """
    Search workflows by name with pagination (case-insensitive).

    Query Parameters:
    - query: Search term for workflow name (required)
    - page: Page number (default: 1)
    - page_size: Number of items per page, max 100 (default: 10)
    """
    user: Users = current_user.get_user()
    session: AsyncSession = current_user.get_session()

    workflows = await workflow_service.search_workflows(
        session=session,
        query=query,
        page=page,
        page_size=page_size,
        user_id=str(user.id) if explore is False else None,
    )
    return SuccessResponse[PaginatedWorkflowsResponse](data=workflows)


@workflow_router.post("/create", response_model=SuccessResponse[WorkflowResponseModel])
async def create_new_workflow(
    workflow_data: CreateNewWorkflowModel,
    current_user: UserAndSessionData = Depends(get_user_and_session),
    workflow_service: WorkflowService = Depends(WorkflowService),
) -> SuccessResponse[WorkflowResponseModel]:
    user: Users = current_user.get_user()
    session: AsyncSession = current_user.get_session()
    workflow = await workflow_service.create_new_workflow(
        session=session, workflow=workflow_data, user_id=str(user.id)
    )

    workflow_response_data = {
        "workflow_id": str(workflow.id),
        "name": workflow.name,
        "description": workflow.description,
        "nodes": workflow.nodes,
        "edges": workflow.edges,
        "visibility": workflow.visibility,
        "created_by": user.username
    }
    return SuccessResponse[WorkflowResponseModel](
        message="Workflow Created Successfully.", data=workflow_response_data
    )


@workflow_router.get(
    "/{workflow_id}", response_model=SuccessResponse[SingleWorkflowResponseModel]
)
async def get_workflow_by_id(
    workflow_id: str,
    current_user: UserAndSessionData = Depends(get_user_and_session),
    workflow_service: WorkflowService = Depends(WorkflowService),
) -> SuccessResponse[SingleWorkflowResponseModel]:
    user: Users = current_user.get_user()
    session: AsyncSession = current_user.get_session()
    workflow = await workflow_service.get_workflow_data(
        session=session, workflow_id=workflow_id, user_id=str(user.id)
    )
    return SuccessResponse[SingleWorkflowResponseModel](
        message="Workflow Returned Successfully.", data=workflow
    )


@workflow_router.post(
    "/star/{workflow_id}", response_model=SuccessResponse[StarWorkflowResponseModel]
)
async def star_workflow(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(WorkflowService),
    current_user: UserAndSessionData = Depends(get_user_and_session),
) -> SuccessResponse[StarWorkflowResponseModel]:
    user: Users = current_user.get_user()
    session: AsyncSession = current_user.get_session()
    workflow = await workflow_service.star_workflow(
        session=session, workflow_id=workflow_id, user_id=str(user.id)
    )
    data = {"workflow_id": str(workflow.id), "stars": workflow.stars}
    
    return SuccessResponse[StarWorkflowResponseModel](
        data=data, message="Workflow starred successfully."
    )


# @workflow_router.get("/run/{workflow_id}")
# async def run_pipeline(
#     workflow_id: str,
#     worflow_service: WorkflowService = Depends(WorkflowService),
#     current_user: UserAndSessionData = Depends(get_user_and_session),
#     temporal_client: client.Client = Depends(TemporalClientManager.get_client),
# ) -> StreamingResponse:
#     user_id: str = decoded_token["sub"]
#     coro = worflow_service.create_new_workflow_run(
#         workflow_id=workflow_id, user_id=user_id
#     )
#     workflow, workflow_run = await safely_run(coro)

#     workflow_input = WorkflowInput(
#         workflow=Workflow(nodes=workflow.nodes, edges=workflow.edges),
#         configs={"user_id": f"{user_id}"},
#     )

#     temporal_wf_id: str = f"{user_id}-{workflow_id}-{str(workflow_run.id)}"

#     workflow_handler = await temporal_client.start_workflow(
#         "DynamicWorkflow",
#         workflow_input,
#         id=temporal_wf_id,
#         task_queue="default",
#     )

#     return StreamingResponse(
#         workflow_listener(temporal_client=temporal_client, workflow_id=temporal_wf_id),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "close",
#         },
#     )
