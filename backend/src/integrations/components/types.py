from src.types.db_types import OAuth2CredentialsModel, ApiKeyCredentialsModel
from typing import TypeAlias, TypedDict, Any, Dict

CredentialsModel: TypeAlias = OAuth2CredentialsModel | ApiKeyCredentialsModel



class RequestOptions(TypedDict):
    data: Dict[str, Any] | None  # Data to be sent for post request www-url-from-encoded
    json: Dict[str, Any] | None  # Data to be sent for post request json-encoded.
    params: Dict[str, str] | None  # Query parameters to send
    headers: Dict[str, Any] | None
    timeout: int | None  # Timeout for the request
