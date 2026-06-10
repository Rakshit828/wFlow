from src.integrations.services.Google.nodes import (
    GET_SINGLE_GMAIL_LABEL_NODE,
    SEND_EMAIL_NODE,
    READ_CELL_VALUES_NODE,
    DRAFT_EMAIL_NODE,
    APPEND_CELL_VALUES_NODE,
    UPDATE_CELL_VALUES_NODE,
    CREATE_GOOGLE_SHEET_NODE,
    LIST_USER_GMAIL_LABELS_NODE,
    UPLOAD_FILE_ON_DRIVE_NODE,
)
from src.integrations.services.llms.nodes import GROQ_LLM_NODE, GOOGLE_LLM_NODE
from src.workflows.control_flow_nodes import IF_NODE, SWITCH_NODE

NODES_MAP = {
    "llm.groq": GROQ_LLM_NODE,
    "llm.google": GOOGLE_LLM_NODE,
    "drive.upload": UPLOAD_FILE_ON_DRIVE_NODE,
    
    "gmail.send": SEND_EMAIL_NODE,
    "gmail.create_draft_email": DRAFT_EMAIL_NODE,

    "gmail.get_label_data": GET_SINGLE_GMAIL_LABEL_NODE,
    "gmail.list_gmail_labels": LIST_USER_GMAIL_LABELS_NODE,

    "sheets.update_cell_values": UPDATE_CELL_VALUES_NODE,
    "sheets.append_cell_values": APPEND_CELL_VALUES_NODE,
    "sheets.read_cell_values": READ_CELL_VALUES_NODE,
    "sheets.create_google_sheet": CREATE_GOOGLE_SHEET_NODE,
    
    "if_node": IF_NODE,
    "switch_node": SWITCH_NODE,
}
