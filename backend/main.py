from src.integrations.services.Google import GoogleAPIClient, CredentialsModel
from src.integrations.services.Google.gmail.webhook import watch_gmail, get_history
from src.domains.app_integrations.repository import AppIntegrationsRepository
from src.domains.app_integrations.types import CredentialsAndDataForApiClient
from src.integrations.services.Google.gmail.types import (
    WatchGmailInput,
    GetGmailHistoryInput,
)
from src.integrations.services.Google.shared import CommonGoogleConfigModel

from src.db.mongo_db import MongoClient


async def main():
    mongo = MongoClient(db_uri="mongodb://localhost:27017")
    await mongo.get_database("wflow_db")
    await mongo.init_beanie_odm()
    integration_repo: AppIntegrationsRepository = AppIntegrationsRepository()

    credentials: CredentialsAndDataForApiClient | None = (
        await integration_repo.find_app_integration(
            user_id="6a1d72e65f99ccba41e1f359",
            provider="google",
            service="gmail",
            projection_model=CredentialsAndDataForApiClient,
        )
    )
    credentials = credentials[0]

    credentials = CredentialsModel(
        user_id=credentials.user_id,
        integration_id=credentials.integration_id,
        service=credentials.service,
        access_token=credentials.access_token,
        refresh_token=credentials.refresh_token,
        scopes=credentials.scopes,
        access_token_expiry=credentials.access_token_expiry,
        refresh_token_expiry=credentials.refresh_token_expiry,
    )

    # result = await watch_gmail(
    #     node_input=WatchGmailInput(
    #         topic_name="projects/aiworkflowautomation/topics/gmail-notifications",
    #         label_ids=["STARRED"],
    #         config=CommonGoogleConfigModel(credentials=credentials, service="gmail"),
    #     )
    # )

    # print(f"\n Output: {result}")

    result = await get_history(
        GetGmailHistoryInput(
            startHistoryId="631188",
            config=CommonGoogleConfigModel(credentials=credentials, service="gmail"),
        )
    )

    print(f"\n History: {result}")


if __name__ == "__main__":
    import asyncio
    import jwt

    print(f"Result is : {result}")
    asyncio.run(main())
