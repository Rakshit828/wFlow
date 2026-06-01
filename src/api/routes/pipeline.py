import uuid
import httpx
from loguru import logger
from typing import Literal
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form

from src.api.dependencies import (
    AccessTokenBearer,
)
from src.config import CONFIG
from src.utils.file_uploads import AsyncLocalStorageClient

pipeline_router = APIRouter()


internal_storage_client = AsyncLocalStorageClient(
    base_storage_dir=CONFIG.LOCAL_STORAGE_PATH
)


@pipeline_router.post("/upload-file")
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
