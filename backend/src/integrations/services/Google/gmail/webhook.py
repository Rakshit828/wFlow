from temporalio import activity
from src.integrations.services.Google.gmail.types import (
    WatchGmailInput,
    GmailApis,
    WatchGmailOutput,
    GetGmailHistoryInput,
)


@activity.defn
async def watch_gmail(node_input: WatchGmailInput) -> WatchGmailOutput:
    api_client = node_input.config.get_google_api_client()
    data = {
        "topicName": node_input.topic_name,
        "labelIds": node_input.label_ids,
    }
    _, json_response = await api_client.request(
        "POST",
        GmailApis.WATCH_GMAIL,
        requires_bearer_token=True,
        data=data,
    )
    return WatchGmailOutput(**json_response)


async def get_history(node_input: GetGmailHistoryInput) -> dict:
    api_client = node_input.config.get_google_api_client()
    params = node_input.model_dump(exclude_none=True, exclude="config", by_alias=True)

    print(f"Params are : {params}")

    _, json_response = await api_client.request(
        "GET", GmailApis.GET_EMAIL_HISTORY, requires_bearer_token=True, params=params
    )
    return json_response


# async def stop_watch_inbox():
#     """
#     Call this endpoint to manually stop Google from sending notifications
#     to your Pub/Sub topic for this user's inbox.
#     """
#     headers = {
#         "Authorization": f"Bearer ",
#         "Content-Length": "0"  # This endpoint expects an empty body
#     }

#     await

#     async with httpx.AsyncClient() as client:
#         # Note the '/stop' at the end instead of '/watch'
#         response = await client.post(
#             f"{GMAIL_API_BASE}/users/me/stop",
#             headers=headers
#         )

#         # Google returns a 204 No Content on a successful stop
#         if response.status_code not in [200, 204]:
#             raise HTTPException(
#                 status_code=response.status_code,
#                 detail=f"Failed to stop watching inbox: {response.text}"
#             )

#         return {"status": "success", "message": "Watch successfully stopped."}
