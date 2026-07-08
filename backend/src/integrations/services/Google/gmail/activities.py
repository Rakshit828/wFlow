import base64
from typing import Any
from src.utils.utils import timer
from src.integrations.services.Google import GoogleRequestHandler
from src.integrations.services.Google.gmail.types import (
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
from src.integrations.components.types import RequestOptions
from src.integrations.services.Google.gmail.helpers import EmailMIMEBuilder
from temporalio import activity


@timer
def decode_base64(text: str) -> str:
    decoded_bytes = base64.urlsafe_b64decode(text)
    clean_text = decoded_bytes.decode("utf-8")
    return clean_text


@activity.defn
async def get_gmail_user_profile(
    service_client: GoogleRequestHandler,
) -> GetUserProfileResponse:
    """
    Fetch the authenticated user's Gmail profile.

    Includes email address, message counts, and storage usage metadata.

    Args:
        service_client: Authenticated GoogleRequestHandler instance.

    Returns:
        GetUserProfileResponse: Parsed Gmail profile response.

    Raises:
        ValueError: If response is empty or malformed.
        Exception: Propagates API/network errors.
    """

    _, response_json = await service_client.handle(
        "GET",
        GmailApis.GET_PROFILE,
    )

    if not response_json:
        raise ValueError("Empty response received from Gmail profile API.")

    return GetUserProfileResponse(**response_json)


@activity.defn
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
    service_client: GoogleRequestHandler = node_input.config.service_handler

    _, response_json = await service_client.handle(
        "GET",
        GmailApis.GET_LABEL.format(id=node_input.label_id),
    )

    if not response_json:
        raise ValueError("Empty response received from Gmail API while listing labels.")

    print(response_json)
    return SingleLabelResponse(**response_json)


@activity.defn
async def list_gmail_labels(
    node_input: ListAllLabelsInput,
) -> ListLabelsResponse:
    """
    Fetch all labels for the authenticated Gmail user.

    Args:
        service_client: Authenticated GoogleRequestHandler instance.
        include_label_ids: Filter labels by specific label IDs.
        max_results: Maximum number of labels to return.
        page_token: Token for paginated results.

    Returns:
        ListLabelsResponse: Parsed response containing label metadata.
    """
    service_client: GoogleRequestHandler = node_input.config.service_handler

    params: dict[str, Any] = {}
    options: RequestOptions = {
        "params": params,
        "data": None,
        "headers": None,
        "json": None,
        "timeout": None
    }

    if node_input.include_label_ids:
        params["includeLabelIds"] = node_input.include_label_ids

    if node_input.max_results:
        params["maxResults"] = node_input.max_results

    if node_input.page_token:
        params["pageToken"] = node_input.page_token

    

    _, response_json = await service_client.handle(
        "GET",
        GmailApis.LIST_LABELS,
        options=options,
    )

    if not response_json:
        raise ValueError("Empty response received from Gmail API while listing labels.")
    print(response_json)
    return ListLabelsResponse(**response_json)


@activity.defn
async def send_email(
    node_input: SendAndDraftEmailInput,
):
    email_builder = EmailMIMEBuilder()
    service_client: GoogleRequestHandler = node_input.config.service_handler

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
    _, response_json = await service_client.handle(
        "POST",
        GmailApis.SEND_MESSAGE,
        options={"json": payload}
    )
    print(response_json)

    return SendAndDraftEmailResponse(success=True)


@activity.defn
async def create_email_draft(node_input: SendAndDraftEmailInput):
    email_builder = EmailMIMEBuilder()
    service_client: GoogleRequestHandler = node_input.config.service_handler

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

    _, response_json = await service_client.handle(
        "POST",
        GmailApis.DRAFT_EMAIL,
        options={"json": payload}
    )
    print(response_json)

    return SendAndDraftEmailResponse(success=True)


async def get_email(
    service_client: GoogleRequestHandler,
    message_id: str,
    format: str = "full",
) -> GmailRawResponse | GmailFullMessage:
    endpoint = GmailApis.GET_MESSAGE_ID.replace("{id}", message_id)

    params = {"format": format}

    response, response_json = await service_client.handle(
        "GET",
        endpoint=endpoint,
        options={"params": params}
    )

    if format == "full":
        return GmailFullMessage(**response_json)
    else:
        return GmailRawResponse(**response_json)


async def list_emails(
    service_client: GoogleRequestHandler,
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

    _, response_json = await service_client.handle(
        "GET",
        GmailApis.LIST_MESSAGES,
        options={"params": params}
    )
    return ReadEmailsIdModel(**response_json)
