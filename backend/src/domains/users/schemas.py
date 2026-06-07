from pydantic import BaseModel
from beanie import PydanticObjectId
from datetime import datetime


class LoginResponse(BaseModel):
    user_id: PydanticObjectId
    email: str
    created_at: datetime


class UserSessionResponse(BaseModel):
    user_id: str
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
