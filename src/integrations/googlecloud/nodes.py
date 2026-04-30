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
    ListAllLabelsInput,
)
from src.workflows.types import ApplicationNode, NodesTypeEnum
from src.integrations.googlecloud.gsheets import (
    create_google_sheet,
    CreateGoogleSheetInput,
    CreateGoogleSheetResponse,
    read_cell_values,
    ReadCellValuesInput,
    ReadCellValuesResponse,
    append_cell_values,
    AppendCellValuesInput,
    AppendCellValuesResponse,
    update_cell_values,
    UpdateCellValuesInput,
    UpdateCellValuesResponse,
)

CREATE_GOOGLE_SHEET_NODE = ApplicationNode(
    key="sheets.create_google_sheet",
    name="create_google_sheet",
    fn=create_google_sheet,
    service="google.sheets",
    valid_permissions=["sheets.fullaccess", "drive.file", "drive.fullaccess"],
    type=NodesTypeEnum.ACTION,
    node_input_model=CreateGoogleSheetInput,
    node_output_model=CreateGoogleSheetResponse,
)

READ_CELL_VALUES_NODE = ApplicationNode(
    key="sheets.read_cell_values",
    name="read_cell_values",
    fn=read_cell_values,
    service="google.sheets",
    valid_permissions=[
        "sheets.fullaccess",
        "drive.file",
        "drive.fullaccess",
        "sheets.readonly",
        "drive.readonly",
    ],
    type=NodesTypeEnum.ACTION,
    node_input_model=ReadCellValuesInput,
    node_output_model=ReadCellValuesResponse,
)

APPEND_CELL_VALUES_NODE = ApplicationNode(
    key="sheets.append_cell_values",
    name="append_cell_values",
    fn=append_cell_values,
    service="google.sheets",
    valid_permissions=[
        "sheets.fullaccess",
        "drive.file",
        "drive.fullaccess",
    ],
    type=NodesTypeEnum.ACTION,
    node_input_model=AppendCellValuesInput,
    node_output_model=AppendCellValuesResponse,
)

UPDATE_CELL_VALUES_NODE = ApplicationNode(
    key="sheets.update_cell_values",
    name="update_cell_values",
    fn=update_cell_values,
    service="google.sheets",
    valid_permissions=[
        "sheets.fullaccess",
        "drive.file",
        "drive.fullaccess",
    ],
    type=NodesTypeEnum.ACTION,
    node_input_model=UpdateCellValuesInput,
    node_output_model=UpdateCellValuesResponse,
)


LIST_USER_GMAIL_LABELS_NODE = ApplicationNode(
    key="gmail.list_gmail_labels",
    name="list_gmail_labels",
    fn=list_gmail_labels,
    service="google.gmail",
    valid_permissions=[
        "gmail.readonly",
        "gmail.fullaccess",
        "gmail.metadata",
        "gmail.labels",
        "gmail.modify",
    ],
    description="Lists all built-in and user-defined Gmail labels.",
    type=NodesTypeEnum.ACTION,
    node_input_model=ListAllLabelsInput,
    node_output_model=ListLabelsResponse,
)

GET_SINGLE_GMAIL_LABEL_NODE = ApplicationNode(
    key="gmail.get_lable_data",
    name="get_gmail_label_data",
    fn=get_gmail_label_data,
    service="google.gmail",
    valid_permissions=[
        "gmail.readonly",
        "gmail.fullaccess",
        "gmail.metadata",
        "gmail.labels",
        "gmail.modify",
    ],
    description="Fetch details of a specific Gmail label by ID.",
    type=NodesTypeEnum.ACTION,
    node_input_model=GetSingleLableInput,
    node_output_model=SingleLabelResponse,
)

SEND_EMAIL_NODE = ApplicationNode(
    key="gmail.send_email",
    name="send_email",
    fn=send_email,
    service="google.gmail",
    valid_permissions=[
        "gmail.fullaccess",
        "gmail.modify",
        "gmail.compose",
        "gmail.send",
    ],
    description="Send emails according to requirement.",
    type=NodesTypeEnum.ACTION,
    node_input_model=SendAndDraftEmailInput,
    node_output_model=SendAndDraftEmailResponse,
)


DRAFT_EMAIL_NODE = ApplicationNode(
    key="gmail.create_email_draft",
    name="create_email_draft",
    fn=create_email_draft,
    service="google.gmail",
    valid_permissions=["gmail.fullaccess", "gmail.modify", "gmail.compose"],
    description="Send emails according to requirement.",
    type=NodesTypeEnum.ACTION,
    node_input_model=SendAndDraftEmailInput,
    node_output_model=SendAndDraftEmailResponse,
)
