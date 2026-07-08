from src.types.db_types import OAuth2CredentialsModel, ApiKeyCredentialsModel
from typing import TypeAlias, TypedDict, Any, Dict, Optional

CredentialsModel: TypeAlias = OAuth2CredentialsModel | ApiKeyCredentialsModel


class RequestOptions(TypedDict):
    data: Optional[
        Dict[str, Any] | Any
    ]  # Data to be sent for post request www-url-from-encoded
    json: Optional[Dict[str, Any]]  # Data to be sent for post request json-encoded.
    params: Optional[Dict[str, Any]]  # Query parameters to send
    headers: Optional[Dict[str, Any]]
    timeout: Optional[int]  # Timeout for the request
