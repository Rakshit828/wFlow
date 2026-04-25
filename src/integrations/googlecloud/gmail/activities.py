import httpx
from src.integrations.googlecloud import GoogleAPIClient

async def read_my_gmails(
    api_client: GoogleAPIClient,
    return_read_emails: bool = False,
):
    response: httpx.Response = await api_client.request(
        "GET",
        "/gmail/v1/users/me/messages",
        requires_bearer_token=True
    )
    print(response)
    


