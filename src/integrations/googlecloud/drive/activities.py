from loguru import logger
import json
from temporalio import activity
from src.utils.file_uploads import AsyncLocalStorageClient
from src.integrations.googlecloud.drive.types import (
    GDriveApis,
    UploadFileDriveInput,
    UploadFileDriveResponse,
)
from src.config import CONFIG


@activity.defn
async def upload_file_on_drive(
    node_input: UploadFileDriveInput,
) -> UploadFileDriveResponse:

    if node_input.content_ref:
        file_bytes: bytes = node_input.content_ref.encode("utf-8")
    elif node_input.filepath_ref:
        internal_storage_client = AsyncLocalStorageClient(
            base_storage_dir=CONFIG.LOCAL_STORAGE_PATH
        )
        file_bytes: bytes = await internal_storage_client.download(
            node_input.filepath_ref
        )
    else:
        file_bytes: bytes = node_input.file_content

    google_api_client = node_input.config.get_google_api_client()
    filename = node_input.filename
    mime_type = node_input.mime_type

    boundary = "temporal_user_upload"

    headers = {
        "Content-Type": f"multipart/related; boundary={boundary}",
    }

    metadata = {"name": filename, "mimeType": mime_type}

    body_parts = [
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n",
        json.dumps(metadata) + "\r\n",
        f"--{boundary}\r\nContent-Type: {mime_type}\r\n\r\n",
        file_bytes,
        f"\r\n--{boundary}--",  # FIXED: Ensured clean syntax positioning around binary blocks
    ]

    # Flatten everything cleanly into structural web transport bytes
    request_body = b"".join(
        [p.encode("utf-8") if isinstance(p, str) else p for p in body_parts]
    )

    params = {"uploadType": "multipart"}

    status_code, json_response = await google_api_client.request(
        method="POST",
        endpoint=GDriveApis.UPLOAD_FILE,
        requires_bearer_token=True,
        headers=headers,
        params=params,
        data=request_body,
    )

    logger.info(f"The original response is : {json_response}")

    return UploadFileDriveResponse(**json_response)
