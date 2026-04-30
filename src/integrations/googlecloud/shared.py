from pydantic import BaseModel, ConfigDict, PrivateAttr
from src.integrations.googlecloud.google_api_client import GoogleAPIClient


class CommonBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, extra="ignore", arbitrary_types_allowed=True
    )


class CommonGoogleConfigModel(CommonBaseModel):
    _google_api_client: GoogleAPIClient = PrivateAttr()

    @classmethod
    def set_client(cls, client: GoogleAPIClient) -> "CommonGoogleConfigModel":
        obj = cls()
        obj._google_api_client = client
        return obj
