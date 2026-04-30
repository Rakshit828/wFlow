import base64

from src.utils.utils import timer
from src.integrations.googlecloud import GoogleAPIClient
from src.integrations.googlecloud.gmail import (
    GmailApis,
    ReadEmailsIdModel,
    GmailFullMessage,
    GmailRawResponse,
    ListLabelsResponse,
    SingleLabelResponse,
    GetUserProfileResponse,
    ListAllLabelsInput,
    GetSingleLableInput,
    SendAndDraftEmailInput,
    SendAndDraftEmailResponse,
)
from src.integrations.googlecloud.gmail.helpers import EmailMIMEBuilder


@timer
def decode_base64(text: str) -> str:
    decoded_bytes = base64.urlsafe_b64decode(text)
    clean_text = decoded_bytes.decode("utf-8")
    return clean_text


async def get_gmail_user_profile(
    api_client: GoogleAPIClient,
) -> GetUserProfileResponse:
    """
    Fetch the authenticated user's Gmail profile.

    Includes email address, message counts, and storage usage metadata.

    Args:
        api_client: Authenticated GoogleAPIClient instance.

    Returns:
        GetUserProfileResponse: Parsed Gmail profile response.

    Raises:
        ValueError: If response is empty or malformed.
        Exception: Propagates API/network errors.
    """

    response, response_json = await api_client.request(
        "GET",
        GmailApis.GET_PROFILE,
        requires_bearer_token=True,
    )

    if not response_json:
        raise ValueError("Empty response received from Gmail profile API.")

    return GetUserProfileResponse(**response_json)


async def get_gmail_label_data(
    node_input: GetSingleLableInput,
) -> SingleLabelResponse:
    """
    Fetch a single label for the authenticated Gmail user.

    Args:
        label_id: Label id to fetch data for.

    Returns:
        SingleLabelsResponse: Parsed response containing label metadata.
    """
    api_client: GoogleAPIClient = node_input.config._gmail_api_client

    _, response_json = await api_client.request(
        "GET",
        GmailApis.GET_LABEL.format(id=node_input.label_id),
        requires_bearer_token=True,
    )

    if not response_json:
        raise ValueError("Empty response received from Gmail API while listing labels.")

    print(response_json)
    return SingleLabelResponse(**response_json)


async def list_gmail_labels(
    node_input: ListAllLabelsInput | None = None,
) -> ListLabelsResponse:
    """
    Fetch all labels for the authenticated Gmail user.

    Args:
        api_client: Authenticated GoogleAPIClient instance.
        include_label_ids: Filter labels by specific label IDs.
        max_results: Maximum number of labels to return.
        page_token: Token for paginated results.

    Returns:
        ListLabelsResponse: Parsed response containing label metadata.
    """
    api_client: GoogleAPIClient = node_input.gmail_api_client
    params = {}

    if node_input.include_label_ids:
        params["includeLabelIds"] = node_input.include_label_ids

    if node_input.max_results:
        params["maxResults"] = node_input.max_results

    if node_input.page_token:
        params["pageToken"] = node_input.page_token

    _, response_json = await api_client.request(
        "GET",
        GmailApis.LIST_LABELS,
        requires_bearer_token=True,
        params=params if params else None,
    )

    if not response_json:
        raise ValueError("Empty response received from Gmail API while listing labels.")
    print(response_json)
    return ListLabelsResponse(**response_json)


@timer
async def send_email(
    node_input: SendAndDraftEmailInput,
):
    email_builder = EmailMIMEBuilder()
    api_client: GoogleAPIClient = node_input.config._gmail_api_client

    email_builder.add_to(node_input.to)
    email_builder.add_cc(node_input.cc)
    email_builder.add_bcc(node_input.bcc)
    email_builder.set_subject(node_input.subject)

    if node_input.body.startswith("<!DOCTYPE html>") or "<html>" in node_input.body:
        email_builder.set_html_body(node_input.body)
    else:
        email_builder.set_text_body(node_input.body)

    email_builder.build()

    payload = email_builder.to_gmail_payload(node_input.thread_id)
    _, response_json = await api_client.request(
        "POST",
        GmailApis.SEND_MESSAGE,
        requires_bearer_token=True,
        json=payload,
    )
    print(response_json)

    return SendAndDraftEmailResponse(success=True)

@timer
async def create_email_draft(node_input: SendAndDraftEmailInput):
    email_builder = EmailMIMEBuilder()
    api_client: GoogleAPIClient = node_input.config._gmail_api_client

    email_builder.add_to(node_input.to)
    email_builder.add_cc(node_input.cc)
    email_builder.add_bcc(node_input.bcc)
    email_builder.set_subject(node_input.subject)

    if node_input.body.startswith("<!DOCTYPE html>") or "<html>" in node_input.body:
        email_builder.set_html_body(node_input.body)
    else:
        email_builder.set_text_body(node_input.body)

    email_builder.build()

    raw = email_builder.to_gmail_payload(node_input.thread_id)
    payload = {"message": raw}

    _, response_json = await api_client.request(
        "POST",
        GmailApis.DRAFT_EMAIL,
        requires_bearer_token=True,
        json=payload,
    )
    print(response_json)

    return SendAndDraftEmailResponse(success=True)


async def get_email(
    api_client: GoogleAPIClient,
    message_id: str,
    format: str = "full",
) -> GmailRawResponse | GmailFullMessage:
    endpoint = GmailApis.GET_MESSAGE_ID.replace("{id}", message_id)

    params = {"format": format}

    response, response_json = await api_client.request(
        "GET",
        endpoint=endpoint,
        requires_bearer_token=True,
        params=params,
    )

    if format == "full":
        return GmailFullMessage(**response_json)
    else:
        return GmailRawResponse(**response_json)


async def list_emails(
    api_client: GoogleAPIClient,
    query: str | None = None,
    max_results: int = 10,
    label_ids: list[str] | None = None,
) -> ReadEmailsIdModel:
    params = {
        "maxResults": max_results,
    }

    if query:
        params["q"] = query

    if label_ids:
        params["labelIds"] = label_ids

    _, response_json = await api_client.request(
        "GET",
        GmailApis.LIST_MESSAGES,
        requires_bearer_token=True,
        params=params,
    )
    return ReadEmailsIdModel(**response_json)
