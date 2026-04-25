from src.integrations.googlecloud import GoogleAPIClient, CredentialsModel
from src.integrations.googlecloud.gmail.activities import read_my_gmails
from src.repositories.app_integrations import AppIntegrationsRepository
from src.schemas.mongo_projections import GetCredentialsOfIntegration

from src.db.mongo_db import MongoClient

async def main():
    mongo = MongoClient(db_uri="mongodb://localhost:27017")
    await mongo.get_database("wflow_db")
    await mongo.init_beanie_odm()


    credentials: (
        GetCredentialsOfIntegration
    ) = await AppIntegrationsRepository().get_credentials_of_service(
        user_id="69ea34d032f5e9adcfbabe33", provider="google", service="gmail"
    )
    print(credentials.access_token)
    api_client = GoogleAPIClient(
        credentials=CredentialsModel(
            access_token="kds6fs73rb",
            refresh_token=credentials.refresh_token,
            scopes=credentials.scopes,
            access_token_expiry=credentials.access_token_expiry,
            refresh_token_expiry=credentials.refresh_token_expiry,
        ),
        
    )
    await read_my_gmails(api_client, return_read_emails=True)
    await api_client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())