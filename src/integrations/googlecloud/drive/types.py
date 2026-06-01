from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    computed_field,
    PrivateAttr,
    model_validator,
)
from typing import Optional, List
from src.config import CONFIG
from datetime import datetime
from typing import List, Literal, Self
from enum import Enum


from src.integrations.googlecloud.shared import CommonBaseModel, CommonGoogleConfigModel


class GDriveApis(str, Enum):
    UPLOAD_FILE = "/upload/drive/v3/files"
    """Create/Upload a new file in the google drive."""


class UploadFileDriveInput(CommonBaseModel):
    """Input for uploading a file to Google Drive."""

    file_content: bytes | None = Field(
        None, description="The binary content of the file to upload."
    )
    content_ref: str | None = Field(
        None,
        description="The content refrence for the file. The content comes from another node.",
    )
    filepath_ref: str | None = Field(
        None,
        description="The path where the file is located. This will be read and uploaded.",
    )
    filename: str = Field(..., description="The name of the file.")
    mime_type: Optional[str] = Field(None, description="The MIME type of the file.")

    @model_validator(mode="before")
    def validate_file_source(self) -> Self:
        if not any([self.file_content, self.content_ref, self.file_path_ref]):
            raise ValueError(
                "At least one of 'file_content', 'file_ref', or 'filepath_ref' must be provided."
            )
        return self


class UploadFileDriveResponse(BaseModel):
    """Output for the file upload activity."""

    file_id: str = Field(..., description="The ID of the uploaded file.")
    web_view_link: str = Field(
        ..., description="The link to view the file in a browser."
    )
    name: str = Field(..., description="The name of the uploaded file.")
    size: int = Field(..., description="The size of the uploaded file in bytes.")
