from src.integrations.googlecloud.gmail import (
    ListLabelsResponse,
    SingleLabelResponse,
    get_gmail_label_data,
    list_gmail_labels,
    send_email,
    create_email_draft,
    SendAndDraftEmailInput,
    SendAndDraftEmailResponse,
    GetSingleLableInput,
    ListAllLabelsInput
)
from src.workflows.types import ApplicationNode, NodesTypeEnum
from bson import ObjectId


LIST_USER_GMAIL_LABELS_NODE = ApplicationNode(
    key="gmail.list_gmail_labels",
    name="list_gmail_labels",
    fn=list_gmail_labels,
    service="google.gmail",
    permission="gmail.readonly",
    description="Lists all built-in and user-defined Gmail labels.",
    type=NodesTypeEnum.ACTION,
    node_input_model=ListAllLabelsInput,
    node_output_model=ListLabelsResponse
)

GET_SINGLE_GMAIL_LABEL_NODE = ApplicationNode(
    key="gmail.get_lable_data",
    name="get_gmail_label_data",
    fn=get_gmail_label_data,
    service="google.gmail",
    permission="gmail.readonly",
    description="Fetch details of a specific Gmail label by ID.",
    type=NodesTypeEnum.ACTION,
    node_input_model=GetSingleLableInput,
    node_output_model=SingleLabelResponse
)

SEND_EMAIL_NODE = ApplicationNode(
    key="gmail.send_email",
    name="send_email",
    fn=send_email,
    service="google.gmail",
    permission="gmail.modify",
    description="Send emails according to requirement.",
    type=NodesTypeEnum.ACTION,
    node_input_model=SendAndDraftEmailInput,
    node_output_model=SendAndDraftEmailResponse
)


DRAFT_EMAIL_NODE = ApplicationNode(
    key="gmail.create_email_draft",
    name="create_email_draft",
    fn=create_email_draft,
    service="google.gmail",
    permission="gmail.modify",
    description="Send emails according to requirement.",
    type=NodesTypeEnum.ACTION,
    node_input_model=SendAndDraftEmailInput,
    node_output_model=SendAndDraftEmailResponse
)
