from src.integrations.googlecloud import GoogleAPIClient, CredentialsModel
from src.repositories.app_integrations import AppIntegrationsRepository
from src.schemas.mongo_projections import CredentialsAndDataForApiClient
from src.integrations.googlecloud.gmail import (
    SendAndDraftEmailInput,
    SendAndDraftEmailResponse,
    CommonGmailConfigModel,
    create_email_draft,
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

    response: SendAndDraftEmailResponse = await create_email_draft(
        SendAndDraftEmailInput(
            to=["bhattarianita2014@gmail.com"],
            subject="Test Email - wFlow",
            body="""<!DOCTYPE html>
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #000;">
    
    <p><strong>Subject:</strong> Job Application for [Position Name]</p>

    <p>Dear Hiring Manager,</p>

    <p>
      I am writing to apply for the position of <strong>[Position Name]</strong> at 
      <strong>[Company Name]</strong>. I am highly interested in contributing to your team and believe my skills and experience align well with the requirements of this role.
    </p>

    <p>
      I have experience in <strong>[your key skills or field]</strong>, with a strong focus on 
      <strong>[specific strengths or achievements]</strong>. In my previous role at 
      <strong>[Previous Company]</strong>, I successfully <strong>[mention a relevant achievement]</strong>, 
      which helped improve <strong>[result or impact]</strong>.
    </p>

    <p>
      I am particularly drawn to this opportunity because <strong>[brief reason related to company or role]</strong>. 
      I am confident that my background and dedication would allow me to make a meaningful contribution to your organization.
    </p>

    <p>
      Please find my resume attached for your review. I would appreciate the opportunity to discuss how my qualifications align with your needs.
      Thank you for your time and consideration.
    </p>

    <p>Sincerely,<br>
      <strong>[Your Name]</strong><br>
      [Your Contact Information]
    </p>

  </body>
</html>""",
            config=CommonGmailConfigModel.set_client(api_client),
        )
    )
    print(response)

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
    import asyncio as aio

    aio.run(main())
