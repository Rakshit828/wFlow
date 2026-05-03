from .types import ApplicationNode
from pydantic import BaseModel


class IfNodeInput(BaseModel):
    condition: str
    values: str | list[str]


class IfNodeOutput(BaseModel):
    decision: bool


class SwitchNodeInput(BaseModel):
    cases: list[str]


class SwitchNodeOutput(BaseModel):
    case: str


async def if_node(node_input: IfNodeInput) -> IfNodeOutput:
    pass


async def switch_node(node_input: SwitchNodeInput) -> SwitchNodeOutput:
    pass


IF_NODE = ApplicationNode(
    key="if_node",
    name="if_node",
    fn=if_node,
    service=None,
    valid_permissions=None,
    description="This node is for conditional branching, either true, or false.",
    type="CONTROL_FLOW",
    node_input_model=IfNodeInput,
    node_output_model=IfNodeOutput,
)

SWITCH_NODE = ApplicationNode(
    key="switch_node",
    name="switch_node",
    fn=switch_node,
    service=None,
    valid_permissions=None,
    description="This node is for branching based on a value. Used when multiple conditions are there.",
    type="CONTROL_FLOW",
    node_input_model=SwitchNodeInput,
    node_output_model=SwitchNodeOutput,
)
