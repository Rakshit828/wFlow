from pydantic import BaseModel, EmailStr, HttpUrl, Field, ConfigDict, computed_field
from typing import Optional, List
from src.config import CONFIG
from datetime import datetime
from typing import List, Literal
from enum import Enum
import base64
from email import message_from_bytes
from email.policy import default
from src.integrations.googlecloud import GoogleAPIClient


class CommonBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )


class MessageHeader(BaseModel):
    name: str
    value: str


class MessagePartBody(CommonBaseModel):
    attachment_id: Optional[str] = Field(default=None, alias="attachmentId")
    size: Optional[int] = None
    data: Optional[str] = None  # Base64url encoded string


class MessagePart(CommonBaseModel):
    part_id: Optional[str] = Field(default=None, alias="partId")
    mime_type: Optional[str] = Field(default=None, alias="mimeType")
    filename: Optional[str] = None
    headers: Optional[List[MessageHeader]] = None
    body: Optional[MessagePartBody] = None
    parts: Optional[List["MessagePart"]] = None  # Recursive


# Needed for recursive model
MessagePart.model_rebuild()


class MessagePayload(CommonBaseModel):
    part_id: Optional[str] = Field(default=None, alias="partId")
    mime_type: Optional[str] = Field(default=None, alias="mimeType")
    filename: Optional[str] = None
    headers: Optional[List[MessageHeader]] = None
    body: Optional[MessagePartBody] = None
    parts: Optional[List[MessagePart]] = None


class GmailFullMessage(CommonBaseModel):
    id: str
    thread_id: str = Field(alias="threadId")
    label_ids: Optional[List[str]] = Field(default=None, alias="labelIds")
    snippet: Optional[str] = None
    history_id: Optional[str] = Field(default=None, alias="historyId")
    internal_date: Optional[str] = Field(default=None, alias="internalDate")
    payload: Optional[MessagePayload] = None
    size_estimate: Optional[int] = Field(default=None, alias="sizeEstimate")
    raw: Optional[str] = None  # Only present if format="raw"


class GmailRawResponse(CommonBaseModel):
    id: str
    thread_id: str = Field(alias="threadId")
    raw: str  # The base64url encoded string

    @computed_field
    @property
    def parsed_raw_gmail(self) -> str:

        # 2. Decode base64url to bytes
        # Gmail uses 'urlsafe' base64, which uses '-' and '_' instead of '+' and '/'
        raw_bytes = base64.urlsafe_b64decode(self.raw)

        # 3. Parse bytes into a Python email object
        # 'policy=default' makes it return an EmailMessage object (modern API)
        mime_msg = message_from_bytes(raw_bytes, policy=default)

        # 4. Access data easily
        print(f"Subject: {mime_msg['subject']}")
        print(f"From: {mime_msg['from']}")

        # Extract the body
        body = ""
        if mime_msg.is_multipart():
            for part in mime_msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_content()
                    break
        else:
            body = mime_msg.get_content()

        return body


class SingleLabelResponse(CommonBaseModel):
    id: str
    name: str
    type: Literal["system", "user"]

    message_list_visibility: Optional[str] = Field(
        default=None,
        alias="messageListVisibility",
    )
    label_list_visibility: Optional[str] = Field(
        default=None,
        alias="labelListVisibility",
    )

    messages_total: Optional[int] = Field(
        default=None,
        alias="messagesTotal",
    )
    messages_unread: Optional[int] = Field(
        default=None,
        alias="messagesUnread",
    )
    threads_total: Optional[int] = Field(
        default=None,
        alias="threadsTotal",
    )
    threads_unread: Optional[int] = Field(
        default=None,
        alias="threadsUnread",
    )


class ListLabelsResponse(CommonBaseModel):
    labels: List[SingleLabelResponse] = Field(default_factory=list)


class GetUserProfileResponse(CommonBaseModel):
    email_address: str = Field(alias="emailAddress")
    messages_total: int = Field(alias="messagesTotal")
    threads_total: int = Field(alias="threadsTotal")
    history_id: str = Field(alias="historyId")


class GmailApis(str, Enum):
    LIST_THREADS = "gmail/v1/users/me/threads"
    """Lists the threads in the user's mailbox."""

    GET_THREAD_BY_ID = "gmail/v1/users/me/threads/{id}"
    """Gets the specified thread and all its messages."""

    # --- MESSAGES (Individual Emails) ---
    LIST_MESSAGES = "gmail/v1/users/me/messages"
    """Lists the messages in the user's mailbox (returns only IDs and threadIds)."""

    GET_MESSAGE_ID = "gmail/v1/users/me/messages/{id}"
    """Gets the specified message including payload, body, and headers."""

    SEND_MESSAGE = "gmail/v1/users/me/messages/send"
    """Sends the specified message (requires raw RFC 2822 formatted email)."""

    DELETE_MESSAGE_ID = "gmail/v1/users/me/messages/{id}/trash"
    """Moves the specified message to the trash."""

    # --- ATTACHMENTS ---
    GET_ATTACHMENT = "gmail/v1/users/me/messages/{messageId}/attachments/{id}"
    """Gets the specified message attachment data."""

    # --- LABELS & METADATA ---
    LIST_LABELS = "gmail/v1/users/me/labels"
    """Lists all labels in the user's mailbox (INBOX, TRASH, SPAM, or custom)."""

    GET_LABEL = "gmail/v1/users/me/labels/{id}"
    """Gets details of a specific label (name, message count, visibility)."""

    MODIFY_MESSAGE_LABELS = "gmail/v1/users/me/messages/{id}/modify"
    """Modifies the labels on the specified message (e.g., marking as 'READ')."""

    # --- USER PROFILE ---
    GET_PROFILE = "gmail/v1/users/me/profile"
    """Gets the current user's Gmail profile (email address, total messages, etc.)."""


class EmailIdsAndThreads(BaseModel):
    id: str
    threadId: str


class ReadEmailsIdModel(BaseModel):
    messages: List[EmailIdsAndThreads]
    nextPageToken: str | None = None
    resultSizeEstimate: int | None = None

    model_config = ConfigDict(extra="ignore")


# All the input models taken by the nodes.
class ListAllLabelsInput(CommonBaseModel):
    gmail_api_client: Optional[GoogleAPIClient] = Field(
        default=None, alias="gmailApiClient"
    )
    include_label_ids: Optional[List[str]] = Field(
        default=None, alias="includeLabelIds"
    )
    max_results: Optional[int] = Field(default=None, alias="maxResults")
    page_token: Optional[str] = Field(default=None, alias="pageToken")


class GetSingleLableInput(CommonBaseModel):
    gmail_api_client: Optional[GoogleAPIClient] = Field(
        default=None, alias="gmailApiClient"
    )
    label_id: str
