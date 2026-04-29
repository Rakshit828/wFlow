from src.integrations.googlecloud.gmail import (
    ListLabelsResponse,
    SingleLabelResponse,
    get_label_data,
    list_labels,
    GetSingleLableInput,
    ListAllLabelsInput
)
from src.workflows.types import Node
from bson import ObjectId


LIST_USER_GMAIL_LABELS_NODE = Node(
    node_id=ObjectId("69ee0680e46453fa19362171"),
    name="list_labels",
    fn=list_labels,
    description="Lists all built-in and user-defined Gmail labels.",
    type="INTEGRATION",
    node_input_model=ListAllLabelsInput,
    node_output_model=ListLabelsResponse
)

GET_SINGLE_GMAIL_LABEL_NODE = Node(
    node_id=ObjectId("69ee0680e46453fa19362172"),
    name="get_label_data",
    fn=get_label_data,
    description="Fetch details of a specific Gmail label by ID.",
    type="INTEGRATION",
    node_input_model=GetSingleLableInput,
    node_output_model=SingleLabelResponse
)

