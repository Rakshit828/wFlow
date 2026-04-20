from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class LoginResponse(BaseModel):
    user_id: UUID
    email: str
    created_at: datetime
