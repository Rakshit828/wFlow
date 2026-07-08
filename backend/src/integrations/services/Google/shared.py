from pydantic import BaseModel, ConfigDict, Field
from src.integrations.services.Google.service_client import GoogleRequestHandler


class CommonBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, extra="ignore", arbitrary_types_allowed=True
    )


class CommonGoogleConfigModel(CommonBaseModel):
    # Data points that can be filled by the users.
    user_id: str = Field(json_schema_extra={"x-autofilled": True})
    service: str = Field(json_schema_extra={"x-autofilled": True})

    # Things processed internally
    service_handler: GoogleRequestHandler = Field(exclude=True)
