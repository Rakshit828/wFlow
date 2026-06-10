from temporalio import activity
from src.integrations.services.Google.gmail.types import (
    WatchGmailInput,
    GmailApis,
    WatchGmailOutput,
    GetGmailHistoryInput,
)



async def get_history(node_input: GetGmailHistoryInput) -> dict:
    api_client = node_input.config.get_google_api_client()
    params = node_input.model_dump(exclude_none=True, exclude="config", by_alias=True)

    print(f"Params are : {params}")

    _, json_response = await api_client.request(
        "GET", GmailApis.GET_EMAIL_HISTORY, requires_bearer_token=True, params=params
    )
    return json_response

async def 