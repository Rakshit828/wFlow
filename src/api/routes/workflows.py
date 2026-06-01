import uuid
from loguru import logger
from typing import Literal
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form

from src.api.dependencies import AccessTokenBearer
from src.config import CONFIG
from src.utils.file_uploads import AsyncLocalStorageClient
from src.schemas.workflow import (
    CreateNewWorkflowModel,
    WorkflowResponseModel,
    StarWorkflowResponseModel,
)
from src.services.workflow_service import WorkflowService

workflow_router = APIRouter()

internal_storage_client = AsyncLocalStorageClient(
    base_storage_dir=CONFIG.LOCAL_STORAGE_PATH
)


@workflow_router.post("/create", response_model=WorkflowResponseModel)
async def create_new_workflow(
    workflow_data: CreateNewWorkflowModel,
    decoded_token: str = Depends(AccessTokenBearer()),
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


@workflow_router.post("/star/{workflow_id}", response_model=StarWorkflowResponseModel)
async def star_workflow(
    workflow_id: str,
    workflow_service: WorkflowService = Depends(WorkflowService),
    decoded_token: str = Depends(AccessTokenBearer()),
) -> StarWorkflowResponseModel:
    user_id: str = decoded_token["sub"]
    workflow = await workflow_service.star_workflow(
        workflow_id=workflow_id, user_id=user_id
    )
    data = {"workflow_id": str(workflow.id), "stars": workflow.stars}
    
    logger.info(f"Data is {data}")
    return data


@workflow_router.post("/upload-file")
async def run_pipeline(user_file: UploadFile = File(None)):  # Optional user upload file
    context_injections = {}

    if user_file:
        file_id = f"file_{uuid.uuid4().hex}"  # Generate unpredictable, distinct key
        file_bytes = await user_file.read()

        await internal_storage_client.upload(
            file_id=file_id, file_bytes=file_bytes, content_type=user_file.content_type
        )

        # Bind file reference key into global metadata context maps
        context_injections["user_uploaded_file"] = file_id

    # 3. Inject this reference context key directly into your Pipeline Model
    # pipeline_obj = Pipeline.model_validate_json(pipeline_json)
    # pipeline_obj.context.update(context_injections)

    # 4. Kick-off to Temporal Workflow engine...
    # await temporal_client.start_workflow(..., args=[pipeline_obj])

    return {"status": "queued", "staged_files": context_injections}
