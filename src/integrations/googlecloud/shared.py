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
        print(f"\n Setting the client. \n")
        obj._google_api_client = client
        print(f"Type is : {type(obj)}")
        print(f"Client is : {obj._google_api_client}")
        return obj
    
    
    def get_client(self) -> GoogleAPIClient:
        return self._google_api_client
    
    