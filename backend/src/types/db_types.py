from typing import Dict, Type, TypeVar
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

Model = TypeVar("Model", bound=BaseModel)


class OAuth2CredentialsModel(BaseModel):
    access_token: str
    refresh_token: str | None
    access_token_expiry: datetime
    refresh_token_expiry: datetime | None = None


class ApiKeyCredentialsModel(BaseModel):
    access_token: str
    expiry: datetime | None = None


class CredentialsTypeEnum(str, Enum):
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"


CREDENTIALS_TYPE_MODEL_MAP: Dict[CredentialsTypeEnum, Type[Model]] = {
    CredentialsTypeEnum.OAUTH2: OAuth2CredentialsModel,
    CredentialsTypeEnum.API_KEY: ApiKeyCredentialsModel,
}


class LoginProvidersEnum(str, Enum):
    GOOGLE = "GOOGLE"
    GITHUB = "GITHUB"


class WorkflowVisibilityEnum(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class WorkflowExecutionStatusEnum(str, Enum):
    STARTED = "STARTED"
    PENDING = "PENDING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
