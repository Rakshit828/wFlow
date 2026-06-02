from pydantic import BaseModel
from beanie import PydanticObjectId
from uuid import UUID
from datetime import datetime


class LoginResponse(BaseModel):
    user_id: PydanticObjectId
    email: str
    created_at: datetime
