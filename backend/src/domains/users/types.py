from pydantic import BaseModel

class UserSessionResponse(BaseModel):
    user_id: str
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
