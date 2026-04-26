from src.integrations.googlecloud import GoogleAPIClient, CredentialsModel
from src.integrations.googlecloud.gmail.activities import (
    list_emails,
    get_email,
    decode_base64,
    list_labels,
    get_label_data,
    get_user_profile
)
from src.repositories.app_integrations import AppIntegrationsRepository
from src.schemas.mongo_projections import CredentialsAndDataForApiClient
from src.integrations.googlecloud import GoogleErrorStatus
from src.integrations.googlecloud.gmail import (
    ReadEmailsIdModel,
    GmailFullMessage,
    GmailRawResponse,
    GetUserProfileResponse,
    SingleLabelResponse,
    ListLabelsResponse,
    EmailIdsAndThreads,
    GmailApis
)

from src.db.mongo_db import MongoClient


async def main():

    mongo = MongoClient(db_uri="mongodb://localhost:27017")
    await mongo.get_database("wflow_db")
    await mongo.init_beanie_odm()
    integration_repo: AppIntegrationsRepository = AppIntegrationsRepository()

    credentials: CredentialsAndDataForApiClient | None = (
        await integration_repo.find_app_integration(
            user_id="69ea34d032f5e9adcfbabe33",
            provider="google",
            service="gmail",
            projection_model=CredentialsAndDataForApiClient,
        )
    )
    credentials = credentials[0]

    api_client = GoogleAPIClient(
        integration_repo=integration_repo,
        req_timeout=30.0,
        base_url="https://gmail.googleapis.com",
        credentials=CredentialsModel(
            user_id=credentials.user_id,
            integration_id=credentials.integration_id,
            service=credentials.service,
            access_token=credentials.access_token,
            refresh_token=credentials.refresh_token,
            scopes=credentials.scopes,
            access_token_expiry=credentials.access_token_expiry,
            refresh_token_expiry=credentials.refresh_token_expiry,
        ),
    )

    profile: GetUserProfileResponse = await get_user_profile(api_client)
    print(profile)


    # labels = await get_label_data(api_client, label_id="CATEGORY_PROMOTIONS")
    # print(labels)

    # response: ReadEmailsIdModel = await list_emails(api_client, query="is:unread", label_ids=["CATEGORY_PROMOTIONS"])
    # total_response = len(response.messages)
    # print(total_response)

    # for i in range(total_response):
    #     emal: GmailFullMessage = await get_email(
    #         api_client, message_id=response.messages[i].id, format="full"
    #     )
    #     print(emal.labelIds)


    await api_client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
