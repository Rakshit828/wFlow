import uuid
from loguru import logger
from typing import Literal
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from src.api.dependencies import AccessTokenBearer
from src.config import CONFIG
from src.utils.file_uploads import AsyncLocalStorageClient
from src.domains.workflows.schema import (
    CreateNewWorkflowModel,
    WorkflowResponseModel,
    StarWorkflowResponseModel,
    PaginatedWorkflowsResponse,
    PaginatedNodesResponse,
    SingleWorkflowResponseModel,
)
from src.workflows.types import NodesTypeEnum, Workflow
from src.domains.workflows.service import WorkflowService
from src.services.temporal_client import TemporalClientManager
from src.workflows.types import WorkflowInput
from temporalio import client
from src.utils.runner import safely_run
from src.core.response import AppError
from src.core.exceptions import UnexpectedServerError

workflow_router = APIRouter()

internal_storage_client = AsyncLocalStorageClient(
    base_storage_dir=CONFIG.LOCAL_STORAGE_PATH
)


@workflow_router.post("/update-node-registry")
async def update_node_registry(
    workflow_service: WorkflowService = Depends(WorkflowService),
):
    await workflow_service.update_node_registry()
    return {"status": "success", "message": "Node registry updated successfully"}


@workflow_router.get("/all-nodes", response_model=PaginatedNodesResponse)
async def get_all_nodes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    workflow_service: WorkflowService = Depends(WorkflowService),
) -> PaginatedNodesResponse:
    return await workflow_service.get_all_nodes(page=page, page_size=page_size)


@workflow_router.get("/nodes/{node_type}", response_model=PaginatedNodesResponse)
async def get_all_nodes_by_type_and_service(
    node_type: NodesTypeEnum,
    service: str = Query(None),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    workflow_service: WorkflowService = Depends(WorkflowService),
):
    return await workflow_service.get_nodes_by_type_and_service(
        node_type=node_type, service=service, page=page, page_size=page_size
    )


@workflow_router.get("/", response_model=PaginatedWorkflowsResponse)
async def get_all_workflows(
    explore: bool = Query(
        False,
        description="Explore = True means exploring the workflows created in application. explore=False means exploring user created workflows.",
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    workflow_service: WorkflowService = Depends(WorkflowService),
    decoded_token: dict[str, str] = Depends(AccessTokenBearer()),
) -> PaginatedWorkflowsResponse:
    """
    Fetch all workflows with pagination.

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Number of items per page, max 100 (default: 10)
    """
    user_id: str | None = None
    if not explore:
        user_id = decoded_token["sub"]

    return await workflow_service.get_all_workflows(
        page=page, page_size=page_size, user_id=user_id
    )


@workflow_router.get("/search", response_model=PaginatedWorkflowsResponse)
async def search_workflows(
    explore: bool = Query(
        False,
        description="Explore = True means exploring the workflows created in application. explore=False means exploring user created workflows.",
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    query: str = Query(..., min_length=1, description="Search query for workflow name"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    workflow_service: WorkflowService = Depends(WorkflowService),
    decoded_token: dict[str, str] = Depends(AccessTokenBearer()),
) -> PaginatedWorkflowsResponse:
    """
    Search workflows by name with pagination (case-insensitive).

    Query Parameters:
    - query: Search term for workflow name (required)
    - page: Page number (default: 1)
    - page_size: Number of items per page, max 100 (default: 10)
    """
    user_id: str | None = None
    if not explore:
        user_id = decoded_token["sub"]

    return await workflow_service.search_workflows(
        query=query, page=page, page_size=page_size, user_id=user_id
    )


@workflow_router.post("/create", response_model=WorkflowResponseModel)
async def create_new_workflow(
    workflow_data: CreateNewWorkflowModel,
    decoded_token: dict[str, str] = Depends(AccessTokenBearer()),
    workflow_service: WorkflowService = Depends(WorkflowService),
) -> WorkflowResponseModel:
    user_id: str = decoded_token["sub"]
    workflow = await workflow_service.create_new_workflow(
        workflow=workflow_data, user_id=user_id
    )

    workflow_response_data = {
        "workflow_id": str(workflow.id),
        "name": workflow.name,
        "description": workflow.description,
        "nodes": workflow.nodes,
        "edges": workflow.edges,
        "visibility": workflow.visibility,
        "created_by": str(workflow.created_by),
    }
    return workflow_response_data


@workflow_router.get("/{workflow_id}", response_model=SingleWorkflowResponseModel)
async def get_workflow_by_id(
    workflow_id: str,
    decoded_token: dict[str, str] = Depends(AccessTokenBearer()),
    workflow_service: WorkflowService = Depends(WorkflowService),
) -> SingleWorkflowResponseModel:
    user_id: str = decoded_token["sub"]
    workflow = await workflow_service.get_workflow_data(
        workflow_id=workflow_id, user_id=user_id
    )
    return workflow


@workflow_router.post("/star/{workflow_id}", response_model=StarWorkflowResponseModel)
async def star_workflow(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(WorkflowService),
    decoded_token: dict[str, str] = Depends(AccessTokenBearer()),
) -> StarWorkflowResponseModel:
    user_id: str = decoded_token["sub"]
    workflow = await workflow_service.star_workflow(
        workflow_id=workflow_id, user_id=user_id
    )
    data = {"workflow_id": str(workflow.id), "stars": workflow.stars}

    logger.info(f"Data is {data}")
    return data


@workflow_router.post("/run/{workflow_id}")
async def run_pipeline(
    workflow_id: str,
    worflow_service: WorkflowService = Depends(WorkflowService),
    decoded_token: dict[str, str] = Depends(AccessTokenBearer()),
    temporal_client: client.Client = Depends(TemporalClientManager.get_client),
):
    user_id: str = decoded_token["sub"]
    coro = worflow_service.create_new_workflow_run(
        workflow_id=workflow_id, user_id=user_id
    )
    workflow, workflow_run = await safely_run(coro)

    workflow_input = WorkflowInput(
        workflow=Workflow(nodes=workflow.nodes, edges=workflow.edges),
        configs={"user_id": f"{user_id}"},
    )

    temporal_wf_id: str = f"{user_id}-{workflow_id}-{str(workflow_run.id)}"

    workflow_handler = await temporal_client.start_workflow(
        "DynamicWorkflow",
        workflow_input,
        id=temporal_wf_id,
        task_queue="default",
    )

    return {
        "message": f"Workflow Started Successfully. {await workflow_handler.describe()}"
    }
