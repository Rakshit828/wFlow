from beanie import Document, Indexed, before_event, Update, PydanticObjectId
from pydantic import Field, ConfigDict
from typing import Optional, List, Annotated
from datetime import datetime, timezone



class AppIntegrations(Document):
    user_id: Annotated[PydanticObjectId, Indexed()]

    provider: Annotated[str, Indexed()]
    service: Annotated[str, Indexed()]
    scopes: List[str] = []

    access_token_enc: str
    access_token_expiry: datetime

    refresh_token_enc: Optional[str] = None
    refresh_token_expiry: Optional[datetime] = None

    metadata: dict | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        name="app_integrations",
        indexes=[
            [("user", 1), ("provider", 1), ("service", 1)],
        ],
    )

    @before_event(Update)
    def set_update(self):
        self.updated_at = datetime.now(tz=timezone.utc)

